#------------------------------------------------------------------------
# 참조 목록.
#------------------------------------------------------------------------
import sys
import importlib.util
import pathlib


extraPaths = [
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/startup",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/modules",
        "C:/Program Files/Blender Foundation/Blender 4.0/python310.zip",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/python/bin",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/python/DLLs",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/python/libs",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/python",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/python/lib/site-packages",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/freestyle/modules",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/addons/modules",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/addons",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/addons_contrib",
        "${userHome}/AppData/Roaming/Python/Python310/site-packages",
        "${userHome}/AppData/Roaming/Blender Foundation/Blender/4.0/scripts/addons/modules",
        "./src"
    ]

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

	index = 0
	for path in sys.path:
		print(f"[{index}] {path}")
		index += 1

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
	for extraPath in extraPaths:
		ImportFromDirectory(extraPath, False)
	# ImportFromDirectory(f"{projectFolder}/src", False)

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