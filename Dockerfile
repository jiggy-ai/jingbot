FROM bitnami/python:3.10-prod   

# set working directory
WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive

#RUN apt-get update && apt-get upgrade -y && apt-get install -y python3-pip ffmpeg
RUN apt-get update && apt-get upgrade -y && apt-get install -y python3-pip 

# update pip
RUN pip3 install --upgrade pip

# add requirements
COPY ./requirements.txt /app/requirements.txt

# install requirements
RUN pip3 install -r requirements.txt

COPY src/* .

# download models
#RUN python3 dl.py  






