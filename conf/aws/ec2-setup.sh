
set -v
set -e

sudo apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y upgrade

sudo apt-get install -y git

mkdir src && cd src
git clone https://github.com/rflynn/productsum.git

