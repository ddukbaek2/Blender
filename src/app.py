#------------------------------------------------------------------------
# 참조 목록.
#------------------------------------------------------------------------
import sys
import importlib.util
import pathlib


extraPaths = [
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/startup",
        "C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/modules",
		"C:/Program Files/Blender Foundation/Blender 4.0/4.0/scripts/modules/bpy",
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
        # "${userHome}/AppData/Roaming/Python/Python310/site-packages",
        # "${userHome}/AppData/Roaming/Blender Foundation/Blender/4.0/scripts/addons/modules",
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
	# 종료 코드 설정.
	exitCode = 0

	# 경로 확인.
	print("sys.path()")
	index = 0
	for path in sys.path:
		print(f"[{index}] {path}")
		index += 1

	# 인자 여부 확인.
	print("arguments()")
	if not len(sys.argv):
		print("[Blender] Argument is empty.")
		exitCode = 1
		sys.exit(exitCode)

	index = 0
	for arg in sys.argv:
		print(f"[{index}] {arg}")
		index += 1

	# 디버그 & 빌드 체크.
	# bpy 참조 오류.
	isDebug = sys.argv[0].find("blender.exe") > -1
	isBuild = getattr(sys, 'frozen', False) # isDebug == False
	
	if isDebug:
		# 디버그모드일 때는 블렌더 기준으로 인자가 잡혀서 0,1,2는 쓸모가 없음.
		sys.argv = sys.argv[3:]

		# 디버거 설정.
		print("Start Blender Debug Server")	
		import debugpy
		debugpy.listen(('localhost', 5680))
		print("Debug server listening on localhost:5680")
		debugpy.wait_for_client()
		print("Debugger client connected")

	applicationFileName = sys.argv[0]
	applicationType = sys.argv[1]
	appArgs = sys.argv[2:]


	# 스크립트 로드.
	executeFilePath = pathlib.Path(__file__).resolve()
	srcPath = executeFilePath.parent
	projectPath = srcPath.parent

	# 스크립트 로드.
	for extraPath in extraPaths:
		ImportFromDirectory(extraPath, False)

	print("app()")
	if applicationType == "conversion_model_validator":
		print("conversion_model_validator()")
		import conversion_model_validator
		exitCode = conversion_model_validator.main(appArgs)
	elif applicationType == "conversion_template_generator":
		print("conversion_template_generator()")
		import conversion_template_generator
		exitCode = conversion_template_generator.main(appArgs)
	else:
		print("unknown_application()")
		exitCode = 1
	
	sys.exit(exitCode)