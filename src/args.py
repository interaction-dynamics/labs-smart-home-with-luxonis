import argparse

# https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse

def str2bool(v):
	if isinstance(v, bool):
		return v
	if v.lower() in ('yes', 'true', 't', 'y', '1'):
		return True
	elif v.lower() in ('no', 'false', 'f', 'n', '0'):
		return False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

def parseArgs():
	parser = argparse.ArgumentParser()
	parser.add_argument('--video', type=str, help="Path to video file to be used for inference instead of luxonis camera")
	parser.add_argument("--remote", type=str2bool, nargs='?', const=True, default=False, help="Activate remote mode")
	parser.add_argument("--host", type=str, default='0.0.0.0', help="ip address of the device")
	parser.add_argument("--port", type=int,default=8080, help="ephemeral port number of the server (1024 to 65535)")
	return parser.parse_args()