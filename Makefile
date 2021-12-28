start:
	python main.py

save:
	dvc add .logs && dvc push -r gdrive