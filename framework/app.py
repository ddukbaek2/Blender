#------------------------------------------------------------------------
# 참조 목록.
#------------------------------------------------------------------------
import sys
import importlib.util
import pathlib


#------------------------------------------------------------------------
# 스크립트 임포트.
#------------------------------------------------------------------------
def ImportFromDirectory(targetPath, isReload = False):
	if not targetPath:
		return
	if not targetPath in sys.path:
		sys.path.append(targetPath)
	elif isReload:
		for moduleName, module in list(sys.modules.items()):
			if hasattr(module, "__file__") and module.__file__ and targetPath in module.__file__:
				del sys.modules[moduleName]
				importlib.import_module(moduleName)
    

#------------------------------------------------------------------------
# 진입점.
#------------------------------------------------------------------------
if __name__ == "__main__":
	
	import debugpy
	debugpy.wait_for_client()

	# 스크립트 로드.
	executeFileName = pathlib.Path(__file__).resolve()
	frameworkFolder = executeFileName.parent
	workspaceFolder = frameworkFolder.parent
	
	# 스크립트 로드.
	ImportFromDirectory(f"{workspaceFolder}/framework", False)
	ImportFromDirectory(f"{workspaceFolder}/src", False)

	if not len(sys.argv):
		print("error.")
	
	index = 0
	for arg in sys.argv:
		print(f"[{index}] {arg}")
		index += 1

	applicationFileName = sys.argv[0]
	applicationType = sys.argv[1].lower()
	appArgs = sys.argv[2:]

  	# # 디버그 서버 실행. 
	# if isDebug:
	# 	import ptvsd # type: ignore
	# 	ptvsd.enable_attach(address = ("localhost", 5680))
	# 	ptvsd.wait_for_attach()

	print("app()")
	if applicationType == "conversion_model_validator":
		print("conversion_model_validator()")
		# import conversion_model_validator
		# conversion_model_validator.main(args)
	elif applicationType == "conversion_template_generator":
		print("conversion_template_generator()")
		# import conversion_template_generator
		# conversion_template_generator.main(args)
	else:
		print("unknown_application()")

	sys.exit()