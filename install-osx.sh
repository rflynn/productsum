#!/bin/bash

# install brew
if ! which brew >/dev/null
then
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
fi

brew update
brew install libffi
brew install libxml2 --with-python

brew install phantomjs
brew install chromedriver

