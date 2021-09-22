# smart-home-with-luxonis
A smart home project using luxonis camera

![Result](https://user-images.githubusercontent.com/4005226/126560171-6d6004da-99b8-4056-a623-07a90025ad01.gif)

A [Medium article](https://medium.com/interaction-dynamics/how-to-use-machine-learning-for-home-automation-with-luxonis-depth-camera-uxtech-1-765418665b5) about this project.

## Getting started

```bash
# manage virtual environement
python3 -m venv .env
source .env/bin/activate

# install dependencies
python3 -m pip install -r requirements.txt

python3 src/smart-home.py
python3 src/smart-home.py --remote # on raspberry pi
python3 src/smart-home.py --video <path> # with a video 

```
