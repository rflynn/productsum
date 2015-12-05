#!/bin/bash

#ssh …
#screen -RR -D
mkdir src && cd src
sudo apt-get install -y git
git clone https://github.com/rflynn/productsum.git
cd productsum
source venv/bin/activate
/bin/bash install.sh
/bin/bash install.sh
sudo /bin/bash install.sh
sudo /bin/bash install.sh
cd product_mapper
time AWS_ACCESS_KEY_ID=AKIAIJSFBGWDARVXQBSA AWS_SECRET_ACCESS_KEY=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 AWS_DEFAULT_REGION=us-east-1 python product2db.py 2>&1

