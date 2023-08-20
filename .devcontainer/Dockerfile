FROM mcr.microsoft.com/devcontainers/base:jammy

# Install texlive-full
RUN apt-get update -y && apt-get install -y --no-install-recommends texlive-full

# Install Python and pip
RUN apt-get update -y && apt-get install -y --no-install-recommends python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip

# Install tools
RUN pip install poetry commitizen

# Install tools
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-key C99B11DEB97541F0 && \
    apt-add-repository https://cli.github.com/packages && \
    apt-get update -y && \
    apt-get install -y gh

# Configure git
RUN git config --global core.editor "code --wait"

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*