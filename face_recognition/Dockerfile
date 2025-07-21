# Stage 1: Compile dlib and install face_recognition
FROM nvidia/cuda:12.4.0-cudnn9-devel AS compile

# Install dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    git \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-numpy \
    gcc \
    build-essential \
    gfortran \
    wget \
    curl \
    # graphicsmagick and libgraphicsmagick1-dev might not be strictly necessary for face_recognition/dlib core
    # If you remove them and face_recognition works, it helps reduce image size.
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    software-properties-common \
    zip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Virtual Environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Scikit-build for dlib
RUN pip install --upgrade pip && \
    pip install scikit-build

# Install dlib with CUDA support
# Consider a more recent dlib version, e.g., 'v19.24' or the latest stable tag
ENV CFLAGS="-static" # Keep static linking for dlib for now. Can be revisited.
RUN git clone -b 'v19.24' --single-branch https://github.com/davisking/dlib.git /dlib && \
    mkdir -p /dlib/build && \
    cd /dlib/build && \
    cmake .. -DDLIB_USE_CUDA=1 -DUSE_AVX_INSTRUCTIONS=1 && \
    cmake --build . && \
    # Install dlib into the virtual environment
    pip install /dlib/build/dlib-*.whl

# Install face_recognition and its dependencies (like opencv-python-headless)
# opencv-python-headless is crucial for server deployments without a GUI
RUN pip install face_recognition opencv-python-headless

# Stage 2: Create the runtime image
FROM nvidia/cuda:12.4.0-cudnn9-runtime

# Install minimal requirements for Python and necessary shared libraries
# python3 is needed to execute /opt/venv/bin/python
# python3-distutils might be needed by some installed python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-distutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy the virtual environment from the compile stage
COPY --from=compile /opt/venv /opt/venv

# Copy necessary shared libraries.
# The exact list might vary slightly with new CUDA versions or if dlib's dependencies change.
# You might need to analyze your dlib build for its dynamic dependencies if issues arise.
# Use 'ldd' on the compiled dlib and any other binaries in the /opt/venv/bin directory
# to get a precise list of required shared libraries.
COPY --from=compile \
    /lib/x86_64-linux-gnu/libpthread.so.0 \
    /lib/x86_64-linux-gnu/libdl.so.2 \
    /lib/x86_64-linux-gnu/librt.so.1 \
    /lib/x86_64-linux-gnu/libX11.so.6 \
    /lib/x86_64-linux-gnu/libpng16.so.16 \
    /lib/x86_64-linux-gnu/libjpeg.so.8 \
    /lib/x86_64-linux-gnu/libstdc++.so.6 \
    /lib/x86_64-linux-gnu/libm.so.6 \
    /lib/x86_64-linux-gnu/libgcc_s.so.1 \
    /lib/x86_64-linux-gnu/libc.so.6 \
    /lib/x86_64-linux-gnu/libxcb.so.1 \
    /lib/x86_64-linux-gnu/libz.so.1 \
    /lib/x86_64-linux-gnu/libXau.so.6 \
    /lib/x86_64-linux-gnu/libXdmcp.so.6 \
    /lib/x86_64-linux-gnu/libbsd.so.0 \
    /lib/x86_64-linux-gnu/

# CUDA libraries
# Note: libcudnn.so.8 is already present in the nvidia/cuda:*-cudnnX-runtime image.
# You might need to adjust these based on the exact CUDA version and what's included in the runtime image.
COPY --from=compile \
    /usr/local/cuda/lib64/libcudart.so.12 \
    /usr/local/cuda/lib64/libcublas.so.12 \
    /usr/local/cuda/lib64/libcurand.so.10 \
    /usr/local/cuda/lib64/libcusolver.so.12 \
    /usr/local/cuda/lib64/libcublasLt.so.12 \
    /usr/local/cuda/lib64/

# Set the PATH for the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

COPY main.py /app/
# If you have other source files, copy them as needed, e.g.:
# COPY ./*.jpg /app/
WORKDIR /app
CMD ["python3", "main.py"]