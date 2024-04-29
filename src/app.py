#------------------------------------------------------------------------
# 참조 목록.
#------------------------------------------------------------------------
import os
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
		print(f"sys.path.append({targetPath})")
	elif isReload:
		if len(sys.modules) > 0:
			for moduleName, module in list(sys.modules.items()):
				# if IsExcludeModules(moduleName):
				# 	continue
				# print(moduleName)
				try:
					if hasattr(module, "__file__") and module.__file__ and targetPath in module.__file__:
						del sys.modules[moduleName]
						importlib.import_module(moduleName)
						print(f"importlib.import_module({moduleName})")
				except Exception as exception:
					# print(f"Reimport Exception ModuleName : '{moduleName}'")
					continue

 
#------------------------------------------------------------------------
# 메인.
#------------------------------------------------------------------------
def Main(args : list) -> int:
	print("app.Main()")
	if applicationType == "conversion_model_validator":
		print("conversion_model_validator()")
		import conversion_model_validator
		return conversion_model_validator.main(appArgs)
	elif applicationType == "conversion_template_generator":
		print("conversion_template_generator()")
		import conversion_template_generator
		return conversion_template_generator.main(appArgs)
	else:
		print("unknown_application()")
		return 1


#------------------------------------------------------------------------
# 파일 진입점.
#------------------------------------------------------------------------
if __name__ == "__main__":
	# 경로 확인.
	print("sys.path()")
	index = 0
	for path in sys.path:
		print(f" - [{index}] {path}")
		index += 1

	# 스크립트 로드.
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
        # "${userHome}/AppData/Roaming/Blender Foundation/Blender/4.0/scripts/addons/modules"
		]
	for extraPath in extraPaths:
		ImportFromDirectory(extraPath, False)

	sourcePath = os.path.dirname(os.path.abspath(__file__))
	projectPath = os.path.dirname(sourcePath)
	if sourcePath not in sys.path:
		sys.path.append(sourcePath)

	# 인자 여부 확인.
	print("arguments()")
	if not len(sys.argv):
		print("[Blender] Argument is empty.")
		sys.exit(1)
	index = 0
	for arg in sys.argv:
		print(f" - [{index}] {arg}")
		index += 1

	# 환경 체크.
	import altava
	altava.Altava.IsBuild = getattr(sys, 'frozen', False)
	print(f"altava.Altava.IsBuild={altava.Altava.IsBuild}")
	altava.Altava.IsDebug = False
	altava.Altava.ProjectPath = projectPath
	print(f"altava.Altava.ProjectPath={altava.Altava.ProjectPath}")
	

	# 빌드일 때.
	if altava.Altava.IsBuild:
		applicationFileName = sys.argv[0] # 실행파일.
		applicationType = sys.argv[1] # 애플리케이션 타입.
		applicationMode = "none" # 애플리케이션 모드.
		sys.argv = sys.argv[2:]
		appArgs = sys.argv

	# VSCODE 실행일 때.
	else:
		# 미사용 인자들 제거.
		sys.argv = sys.argv[3:]
		applicationFileName = sys.argv[0] # 파이썬파일.
		applicationType = sys.argv[2] # 애플리케이션 타입.
		applicationMode = sys.argv[3] # 애플리케이션 모드.
		appArgs = sys.argv[4:]

		#sys.argv[0].find("blender.exe") > -1
		altava.Altava.IsDebug = applicationMode == "debug"
		print(f"altava.Altava.IsDebug={altava.Altava.IsDebug}")

		# 디버그모드일 경우 원격 디버거 실행.
		if altava.Altava.IsDebugMode():
			print("Start Blender Debug Server")	
			import debugpy
			debugpy.listen(('localhost', 5680))
			print("Debug server listening on localhost:5680")
			debugpy.wait_for_client()
			print("Debugger client connected")

	# 시작.
	exitCode = Main(appArgs)
	sys.exit(exitCode)