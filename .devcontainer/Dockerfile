FROM mcr.microsoft.com/devcontainers/base:jammy

# Install texlive-full
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    texlive-base \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-science \
    texlive-lang-italian

# Install Python and pip
RUN apt-get update -y && apt-get install -y --no-install-recommends software-properties-common python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip

# Install tools
RUN pip install poetry commitizen

# Configure git
RUN git config --global core.editor "code --wait"

# Install Docker (including dependencies for Docker-in-Docker)
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get update -y && apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io

# Install act
RUN curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | bash && \
mv bin/act /usr/local/bin/act