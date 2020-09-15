FROM continuumio/anaconda3:latest
ADD housing /code
WORKDIR /code
RUN conda -V && conda config --set channel_priority flexible
COPY pkg_require /home/doc/pkg_require
RUN cd /home/doc/pkg_require
RUN conda install /home/doc/requirements2.txt
RUN pip3 install -r /home/doc/requirements.txt
CMD python /code/housing/housing/main.py
