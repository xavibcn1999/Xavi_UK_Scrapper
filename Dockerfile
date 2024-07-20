# Dockerfile
FROM scrapinghub/scrapinghub-stack-scrapy:1.7-py3

ENV PYTHONUSERBASE=/app/python

# Actualizar pip a la última versión
RUN pip install --upgrade pip

ADD eggbased-entrypoint shub-build-egg shub-list-scripts /usr/local/sbin/
ADD run-pipcheck /usr/local/bin/

RUN chmod +x /usr/local/bin/run-pipcheck \
              /usr/local/sbin/shub-build-egg \
              /usr/local/sbin/shub-list-scripts \
              /usr/local/sbin/eggbased-entrypoint

RUN ln -sf /usr/local/sbin/eggbased-entrypoint /usr/local/sbin/start-crawl && \
    ln -sf /usr/local/sbin/eggbased-entrypoint /usr/local/sbin/scrapy-list && \
    ln -sf /usr/local/sbin/eggbased-entrypoint /usr/local/sbin/shub-image-info && \
    ln -sf /usr/local/sbin/eggbased-entrypoint /usr/local/sbin/run-pipcheck

ADD requirements.txt /app/requirements.txt

RUN mkdir $PYTHONUSERBASE && chown nobody:nogroup $PYTHONUSERBASE

RUN sudo -u nobody -E PYTHONUSERBASE=$PYTHONUSERBASE -E PIP_NO_CACHE_DIR=0 \
    pip install --user --no-cache-dir -r /app/requirements.txt

ADD project /tmp/project
RUN shub-build-egg /tmp/project

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
