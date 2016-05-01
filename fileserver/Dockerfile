FROM debian:stable

RUN apt-get update && apt-get -y install apache2 && apt-get clean
ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
COPY ./apache2.conf /etc/apache2/

RUN mkdir /storage
RUN chown www-data /storage

RUN /usr/sbin/a2enmod dav
RUN /usr/sbin/a2enmod dav_fs
RUN service apache2 restart

EXPOSE 80
EXPOSE 443

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
