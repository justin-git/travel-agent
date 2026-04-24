FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama using the official installation script
RUN curl -fsSL https://ollama.com/install.sh | sh

# Expose Ollama's default port
EXPOSE 11434

# Ensure the Ollama binary is in the path and pull the model
# We start the server in the background, wait for it to be ready, pull the model, then kill the server
RUN ollama serve & sleep 10 && ollama pull gemma4:e4b

# Set the default entrypoint to serve the model
ENTRYPOINT ["ollama", "serve"]
