FROM python:3.6
LABEL maintainer="Semen Borin <mrblooomberg@gmail.com>"
ENV PYTHONUNBUFFERED 0
RUN apt-get update -y &&\
    apt-get install -y tzdata \
 && cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime
COPY ./requirements /trek/requirements
WORKDIR /trek
RUN pip install -r requirements
COPY ./ /trek
ENTRYPOINT [ "python" ]
CMD [ "trek.py" ]