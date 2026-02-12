FROM ghcr.io/cabinlab/claude-code-sdk-docker:python

# Switch to root for installations
USER root

# Install dependencies from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Set up writable cache directories for claude user
ENV PRISMA_PYTHON_CACHE_DIR="/home/claude/.cache/prisma-python"
RUN mkdir -p /home/claude/.cache/prisma-python && \
    chown -R claude:claude /home/claude/.cache

# Generate Prisma client as the non-root runtime user so binary paths resolve under /home/claude.
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

# Copy application code with proper ownership.
# LiteLLM resolves custom_handler paths relative to /app/config.
COPY --chown=claude:claude config/ /app/config/
COPY --chown=claude:claude providers/ /app/config/providers/

# Copy entrypoint script
COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

# Switch back to claude user
USER claude

# Working directory
WORKDIR /app

# Expose LiteLLM port
EXPOSE 4000

# Health check (avoid curl dependency; include auth for protected endpoint)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python3 -c 'import os, urllib.request; req = urllib.request.Request("http://localhost:4000/health/readiness", headers={"Authorization": "Bearer " + os.environ.get("LITELLM_MASTER_KEY", "")}); urllib.request.urlopen(req, timeout=5)' || exit 1

# Single entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
