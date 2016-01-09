#!/bin/bash


# ref: http://www.learnopencv.com/install-opencv-3-on-yosemite-osx-10-10-x/
brew tap homebrew/science
brew install opencv3 --with-contrib --with-tbb #--with-cuda --with-ffmpeg --with-qt5

<<OUTPUT
[ryanflynn@Ryans-MacBook-Air ~/src/productsum/search]$ brew install opencv3 --with-contrib --with-tbb
==> Installing opencv3 from homebrew/science
==> Using Homebrew-provided fortran compiler.
This may be changed by setting the FC environment variable.
==> Downloading https://github.com/Itseez/opencv/archive/3.0.0.tar.gz
==> Downloading from https://codeload.github.com/Itseez/opencv/tar.gz/3.0.0
######################################################################## 100.0%
==> Downloading https://github.com/Itseez/opencv_contrib/archive/3.0.0.tar.gz
==> Downloading from https://codeload.github.com/Itseez/opencv_contrib/tar.gz/3.0.0
######################################################################## 100.0%
==> Downloading https://downloads.sourceforge.net/project/opencvlibrary/3rdparty/ippicv/ippicv_macosx_20141027.tgz
==> Downloading from http://tcpdiag.dl.sourceforge.net/project/opencvlibrary/3rdparty/ippicv/ippicv_macosx_20141027.tgz
######################################################################## 100.0%
==> cmake .. -DCMAKE_C_FLAGS_RELEASE= -DCMAKE_CXX_FLAGS_RELEASE= -DCMAKE_INSTALL_PREFIX=/usr/local/Cellar/opencv3/3.0.0 -DCMAKE_BUILD_TYPE=Release -DCMAKE_FIND_FRAMEWORK=LAST -
==> make
==> make install
==> Caveats
This formula is keg-only, which means it was not symlinked into /usr/local.

opencv3 and opencv install many of the same files.

Generally there are no consequences of this for you. If you build your
own software and it requires this formula, you'll need to add to your
build variables:

    LDFLAGS:  -L/usr/local/opt/opencv3/lib
    CPPFLAGS: -I/usr/local/opt/opencv3/include


If you need Python to find bindings for this keg-only formula, run:
  echo /usr/local/opt/opencv3/lib/python2.7/site-packages >> /usr/local/lib/python2.7/site-packages/opencv3.pth
==> Summary
�  /usr/local/Cellar/opencv3/3.0.0: 350 files, 108M, built in 20.0 minutes
OUTPUT
















<<WORKSBUTOLDER
# ref: http://www.pyimagesearch.com/2015/06/15/install-opencv-3-0-and-python-2-7-on-osx/

#brew install cmake pkg-config
#brew install jpeg libpng libtiff openexr
#brew install eigen tbb


# ref: http://www.mobileway.net/2015/02/14/install-opencv-for-python-on-mac-os-x/

brew tap homebrew/ecience
brew install opencv

mkdir -p /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages
echo 'import site; site.addsitedir("/usr/local/lib/python2.7/site-packages")' >> /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages/homebrew.pth

pip install numpy
sudo pip install matplotlib
WORKSBUTOLDER

<<FUCKED
GCC has been built with multilib support. Notably, OpenMP may not work:
  https://gcc.gnu.org/bugzilla/show_bug.cgi?id=60670
If you need OpenMP support you may want to
  brew reinstall gcc --without-multilib
==> Summary
�  /usr/local/Cellar/gcc/5.3.0: 1361 files, 257M
==> Installing homebrew/science/opencv dependency: homebrew/python/numpy
==> Downloading https://homebrew.bintray.com/bottles-python/numpy-1.10.1.yosemite.bottle.tar.gz
######################################################################## 100.0%
==> Pouring numpy-1.10.1.yosemite.bottle.tar.gz
==> Caveats
Python modules have been installed and Homebrew's site-packages is not
in your Python sys.path, so you will not be able to import the modules
this formula installed. If you plan to develop with these modules,
please run:
  mkdir -p /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages
  echo 'import site; site.addsitedir("/usr/local/lib/python2.7/site-packages")' >> /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages/homebrew.pth
==> Summary
�  /usr/local/Cellar/numpy/1.10.1: 457 files, 9.8M
==> Installing homebrew/science/opencv
==> Downloading https://homebrew.bintray.com/bottles-science/opencv-2.4.12.yosemite.bottle.1.tar.gz
######################################################################## 100.0%
==> Pouring opencv-2.4.12.yosemite.bottle.1.tar.gz
==> Caveats
Python modules have been installed and Homebrew's site-packages is not
in your Python sys.path, so you will not be able to import the modules
this formula installed. If you plan to develop with these modules,
please run:
  mkdir -p /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages
  echo 'import site; site.addsitedir("/usr/local/lib/python2.7/site-packages")' >> /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages/homebrew.pth
==> Summary
�  /usr/local/Cellar/opencv/2.4.12: 225 files, 36M
[ryanflynn@Ryans-MacBook-Air ~/src/productsum/search]$ mkdir -p /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages
[ryanflynn@Ryans-MacBook-Air ~/src/productsum/search]$ echo 'import site; site.addsitedir("/usr/local/lib/python2.7/site-packages")' >> /Users/ryanflynn/Library/Python/2.7/lib/python/site-packages/homebrew.pth
FUCKED
