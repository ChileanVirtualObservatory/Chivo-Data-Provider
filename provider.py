import web
import os
import sys
from os.path import join
import glob
import tarfile
import datetime, time
import optparse
import logging
from wsgilog import WsgiLog
import uuid
import psycopg2
from configparser import ConfigParser
from time import gmtime, strftime

pjoin = os.path.join
runtime_dir = pjoin('/data/chivo_provider_files/')
fitsPath = pjoin('/data/data_pub/fits_delivery_pub/files/')
pathTarballsTemp=pjoin('/data/chivo_provider_files/tarballs/')
pathLog=pjoin('/data/chivo_provider_files/log/')
pathconfdb=pjoin(runtime_dir,'config.ini')

portApp=9000

def read_db_postgres_config(filename=pathconfdb, section='postgres'):
  parser = ConfigParser()
  parser.read(filename)
 
  db = {}
  if parser.has_section(section):
      items = parser.items(section)
      for item in items:
          db[item[0]] = item[1]
  else:
      raise Exception('{0} not found in the {1} file'.format(section, filename))
 
  return db


tarballs=[]

urls = (
  '/fitsprovider', 'FitsProvider',
  '/error', 'Error',
  '/notfound', 'NotFound'
)

class FileLog(WsgiLog):
  def __init__(self, application):
    WsgiLog.__init__(
        self,
        application,
        logformat = '[%(asctime)s][%(name)s][%(levelname)s]: %(message)s',
        debug = True,
        tofile = web.config.log_tofile,
        toprint =  False,
        file = web.config.log_file,
        loglevel = logging.DEBUG
        )
  def __call__(self, environ, start_response):
    def hstart_response(status, response_headers, *args):
      out = start_response(status, response_headers, *args)
      try:
        logline=environ["SERVER_PROTOCOL"]+" "+environ["REQUEST_METHOD"]+" "+environ["REQUEST_URI"]+" - "+status

      except err:
        logline="Could not log <%s> due to err <%s>" % (str(environ), err)

      self.logger.info(logline)

      return out

    return super(FileLog, self).__call__(environ, hstart_response)


def filesPathsXmous(mous_in):
    return_var=[]
    query = """SELECT DISTINCT name_file FROM fits_files_main,pipeline_archive_request_information,coordinate_information \
            WHERE pipeline_archive_request_information.idpipeline_archive_request_information=fits_files_main.pipeline_archive_request_information_id_forean AND coordinate_information.id_coordinate_information=fits_files_main. coordinate_information_id_forean \
            AND pipeline_archive_request_information.member= '%s' """
#            AND coordinate_information.OBSRA=%s \
#            AND coordinate_information.OBSDEC=%s \

    try:
        db_config = read_db_postgres_config()
        conn = psycopg2.connect(**db_config)

        cursor = conn.cursor()
        #cursor.execute(query%(ra_in,dec_in,mous_in))
        cursor.execute(query%(mous_in))

        rows = cursor.fetchall()
        for row in rows:
            return_var.append(pjoin(fitsPath,row[0]))

        cursor.close()
        conn.close()
    except Exception as error:
        return_var=error
    
    finally:
        return(return_var)


def packTarball(files,nameFile):
  pathTarball=pjoin(pathTarballsTemp,"%s.tar.gz"%nameFile)
  tar = tarfile.open(pathTarball, "w:gz")
  for file in files:
    tar.add(file,arcname = file.split("/")[-1])
  tar.close()
  return(pathTarball)

#http://vo.chivo.cl:9000/fitsprovider?mous=A001_X147_X2a6&ra=259.4001208333&dec=-33.70245555556   #423kb
#http://vo.chivo.cl:9000/fitsprovider?mous=A001_X147_X29a&ra=261.2&dec=-34.2                      #4.7GB arriba
#http://vo.chivo.cl:9000/fitsprovider?mous=A001_X144_X81&ra=194.046525&dec=-5.789316666667        #1.9MB
#http://10.6.91.206:8080/fitsprovider?mous=A002_X628157_X5&ra=0.4888333333333&dec=-15.44708333333
class FitsProvider(object):
  def GET(self):
    user_data = web.input()
    mous_in=user_data.mous
    #ra_in=user_data.ra
    #dec_in=user_data.dec
    files_found = filesPathsXmous(mous_in)
    tarForDown=packTarball(files_found,mous_in)
    if len(files_found)!=0:
      try:
        web.header('Content-Disposition', 'attachment; filename={} '.format(tarForDown.split("/")[-1]))
        web.header("Content-Type", 'application/octet-stream')
        web.header('Transfer-Encoding','chunked')
        f = f = open(tarForDown, 'rb')
        while 1:
          buf = f.read(1024 * 8)
          if not buf:
            break
          yield buf
      except:
        pass
        raise web.redirect('/error')
                    
    else:
      raise web.redirect('/notfound')


class Error(object):
  def GET(self):
    return '''<h1>File doesn't exist, please go back.</h1>'''

class NotFound(object):
  def GET(self):
    return '<h1>File not found.</h1>'
    

if __name__ == "__main__":
  render_templates_path = pjoin('/data/chivo_provider_files/templates/')
  render = web.template.render(render_templates_path)
  app = web.application(urls, globals())
  
  nameLogFile=str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))+str(uuid.uuid4())+".log"
  web.config.log_file = pjoin(pathLog,nameLogFile)
  web.config.log_toprint = False
  web.config.log_tofile = True
  web.httpserver.runsimple(app.wsgifunc(FileLog), ("0.0.0.0", portApp))
