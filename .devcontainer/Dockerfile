FROM mcr.microsoft.com/devcontainers/base:jammy

# Install texlive-full
RUN apt-get update -y && apt-get install -y --no-install-recommends texlive-base

# Install Python and pip
RUN apt-get update -y && apt-get install -y --no-install-recommends software-properties-common python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip

# Install tools
RUN pip install poetry commitizen

# Configure git
RUN git config --global core.editor "code --wait"