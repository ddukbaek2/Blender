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

	if not len(sys.argv):
		print("[Blender] Argument is empty.")
		sys.exit()

	index = 0
	for arg in sys.argv:
		print(f"[{index}] {arg}")
		index += 1

	# 스크립트 로드.
	executeFileName = pathlib.Path(__file__).resolve()
	frameworkFolder = executeFileName.parent
	projectFolder = frameworkFolder.parent

	# 디버그.
	# bpy 참조 오류.
	applicationFileName = sys.argv[0]
	# projectFolder = sys.argv[1]
	applicationType = sys.argv[2]
	appArgs = sys.argv[3:]

	# # 실행파일.
	# applicationFileName = sys.argv[0]
	# applicationType = sys.argv[1].lower()
	# appArgs = sys.argv[2:]

	# 스크립트 로드.
	if projectFolder != "build":
		ImportFromDirectory(f"{projectFolder}/framework", False)
		ImportFromDirectory(f"{projectFolder}/src", False)

	print("app()")
	if applicationType == "conversion_model_validator":
		print("conversion_model_validator()")
		import conversion_model_validator
		conversion_model_validator.main(appArgs)
	elif applicationType == "conversion_template_generator":
		print("conversion_template_generator()")
		import conversion_template_generator
		conversion_template_generator.main(appArgs)
	else:
		print("unknown_application()")

	sys.exit()