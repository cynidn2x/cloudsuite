FROM cloudsuite/base-os:ubuntu
ENV DEBIAN_FRONTEND noninteractive

USER root

ENV VERSION 8.1

RUN apt-get update && \
    apt-get install -y --force-yes software-properties-common && \
# if you want to install versions other than 8.1, uncomment the following lines
#    add-apt-repository ppa:ondrej/php && \
#    apt-get update && \
    apt-get install -y --force-yes \
    build-essential \
    vim git wget \
    nginx \
    php${VERSION} php${VERSION}-gd \
    php${VERSION}-mysql php${VERSION}-curl \
    php${VERSION}-fpm php${VERSION}-memcached\
    php${VERSION}-xml \
    php${VERSION}-pdo php${VERSION}-mbstring 
#    php${VERSION}-json   
RUN apt-get install -y --force-yes \
    libnginx-mod-http-vhost-traffic-status || \
    (apt-get install -y --force-yes \
    libpcre3-dev zlib1g-dev libssl-dev && \
    NGINX_VERSION=$(nginx -v 2>&1 | grep -oP '(?<=nginx/)[0-9.]+') && \
    cd /tmp && \
    wget https://github.com/vozlt/nginx-module-vts/archive/v0.2.1.tar.gz -O nginx-module-vts.tar.gz && \
    tar zxvf nginx-module-vts.tar.gz && \
    wget http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    tar zxvf nginx-${NGINX_VERSION}.tar.gz && \
    cd nginx-${NGINX_VERSION} && \
    ./configure --with-compat --add-dynamic-module=/tmp/nginx-module-vts-0.2.1 && \
    make modules && \
    cp objs/ngx_http_vhost_traffic_status_module.so /usr/lib/nginx/modules/ && \
    cd / && rm -rf /tmp/nginx* && \
    echo "load_module modules/ngx_http_vhost_traffic_status_module.so;" > /etc/nginx/modules-enabled/50-mod-http-vhost-traffic-status.conf)
# Increase the open file limit
COPY files/limits.conf.append /tmp/
RUN cat /tmp/limits.conf.append >> /etc/security/limits.conf && rm -f /tmp/limits.conf.append

# Checkout the Elgg installation
RUN mkdir /usr/share/nginx/html/elgg && \ 
    wget --progress=bar:force -O - http://datasets.epfl.ch/cloudsuite/elgg_installation_4.3.0.tar.gz | \
    tar zxvf - -C ~ && \
    mv ~/elgg_installation_4.3.0/* /usr/share/nginx/html/elgg/.
   
WORKDIR /usr/share/nginx/html

# Copy over the settings.php
COPY files/settings_4.3.php elgg/elgg-config/settings.php

# Make the Elgg data directory
RUN mkdir /elgg_data
RUN chmod a+rw /elgg_data

# Copy over the Nginx Server configuration
COPY files/nginx_sites_avail_pt.append /tmp/
COPY files/nginx_sites_avail_tls.append /tmp/


RUN service nginx restart

RUN service php${VERSION}-fpm start

ADD bootstrap.sh /etc/bootstrap.sh
RUN chown root:root /etc/bootstrap.sh
RUN chmod 700 /etc/bootstrap.sh

EXPOSE 8080
EXPOSE 8443

CMD ["/etc/bootstrap.sh", "-d"]
