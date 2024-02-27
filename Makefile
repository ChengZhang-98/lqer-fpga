SHELL = /bin/bash
.PHONY:init
init:
	mkdir -p software/{src,data}
	mkdir -p hardware/{prj,user}
	mkdir -p hardware/user/{ip,data}

.PHONY: update-verible-filelist
update-verible-filelist:
	find hardware/user/components -name "*.sv" -o -name "*.svh" -o -name "*.v" | sort > verible.filelist