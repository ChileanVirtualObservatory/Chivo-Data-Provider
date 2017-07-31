# Service for Provider


```{r, engine='bash', count_lines}
# Create the file
$ sudo touch /etc/init.d/chivoprovider
$ sudo chmod +x /etc/init.d/chivoprovider
# Start chivoprovider
$ sudo service chivoprovider start
# Stop chivoprovider
$ sudo service chivoprovider stop
# Start chivoprovider on boot
$ sudo update-rc.d chivoprovider defaults
# Or use rcconf to manage services http://manpages.ubuntu.com/manpages/natty/man8/rcconf.8.html
$ sudo rcconf
```
