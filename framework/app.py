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
	# 스크립트 로드.
	executeFileName = pathlib.Path(__file__).resolve()
	frameworkFolder = executeFileName.parent
	workspaceFolder = frameworkFolder.parent
	
	# 스크립트 로드.
	ImportFromDirectory(f"{workspaceFolder}/framework", False)
	ImportFromDirectory(f"{workspaceFolder}/src", False)

	if not len(sys.argv):
		print("error.")
	
	applicationType = sys.argv[0].lower()
	isDebug = sys.argv[1].lower() == "true"
 
  	# # 디버그 서버 실행. 
	# if isDebug:
	# 	import ptvsd # type: ignore
	# 	ptvsd.enable_attach(address = ("localhost", 5680))
	# 	ptvsd.wait_for_attach()
	# import ptvsd # type: ignore
	# ptvsd.enable_attach(address = ("localhost", 5680))
	# ptvsd.wait_for_attach()

	# 실행파일 호출.
	args = sys.argv[2:]
	print("hello blender")
	# if applicationType == "conversion_model_validator":
	# 	print("conversion_model_validator()")
	# 	import conversion_model_validator
	# 	conversion_model_validator.main(args)
	# elif applicationType == "conversion_template_generator":
	# 	print("conversion_template_generator()")
	# 	import conversion_template_generator
	# 	conversion_template_generator.main(args)