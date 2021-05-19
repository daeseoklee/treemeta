from glob import glob 

def main():
	n=0
	for name in glob('*.py'):
		n+=len(open(name).readlines())
	for name in glob('*.kv'):
		n+=len(open(name).readlines())
	print(n)
if __name__=='__main__':
	main()
