FROM ghcr.io/cabinlab/claude-code-sdk-docker:python

USER root

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Prisma cache must be writable by the non-root runtime user
ENV PRISMA_PYTHON_CACHE_DIR="/home/claude/.cache/prisma-python"
RUN mkdir -p /home/claude/.cache/prisma-python && \
    chown -R claude:claude /home/claude/.cache

# Generate Prisma client as claude so binary paths resolve under /home/claude
ENV PATH="/opt/venv/bin:$PATH"
RUN chown -R claude:claude /opt/venv/lib/python3.11/site-packages/prisma && \
    su -s /bin/bash claude -c 'cd /opt/venv/lib/python3.11/site-packages/litellm/proxy && \
    HOME=/home/claude PRISMA_PYTHON_CACHE_DIR=/home/claude/.cache/prisma-python prisma generate' && \
    chown -R claude:claude /home/claude/.cache/prisma-python && \
    chmod -R 755 /opt/venv/lib/python3.11/site-packages/prisma && \
    if [ -d /opt/venv/lib/python3.11/site-packages/litellm/proxy/_experimental/out ]; then \
      chown -R claude:claude /opt/venv/lib/python3.11/site-packages/litellm/proxy/_experimental/out && \
      chmod -R u+rwX,go+rX /opt/venv/lib/python3.11/site-packages/litellm/proxy/_experimental/out; \
    fi

# LiteLLM resolves custom_handler paths relative to /app/config
COPY --chown=claude:claude config/ /app/config/
COPY --chown=claude:claude providers/ /app/config/providers/

COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

USER claude
WORKDIR /app
EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python3 -c 'import os, urllib.request; req = urllib.request.Request("http://localhost:4000/health/readiness", headers={"Authorization": "Bearer " + os.environ.get("LITELLM_MASTER_KEY", "")}); urllib.request.urlopen(req, timeout=5)' || exit 1

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
