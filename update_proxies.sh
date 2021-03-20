#!/bin/bash

config_file=/etc/proxychains.conf
work_dir=/home/w00fmeow/workspace/projects/proxy_scraper
live_proxies=$work_dir/live_proxies.txt
clean_config=$work_dir/proxychains_clean_config.txt

echo "Starting to scrape proxies"
sudo service tor start && \
echo "Tor service started" && \
python3 $work_dir/proxy_scraper.py && \
echo "Finished to scrape proxies" && \
cat $clean_config > $config_file && \
echo "Clean config is loaded" && \
cat $live_proxies >> $config_file && \
echo "Proxies loaded to .conf file"

sudo rm $live_proxies