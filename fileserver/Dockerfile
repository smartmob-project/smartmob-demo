FROM debian:stable

RUN apt-get update && apt-get -y install apache2 && apt-get clean
ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
COPY ./001-storage.conf /etc/apache2/sites-enabled/.

RUN mkdir /storage
RUN chown www-data /storage

RUN /usr/sbin/a2enmod dav
RUN /usr/sbin/a2enmod dav_fs

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
