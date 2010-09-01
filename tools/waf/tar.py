import Utils
import tarfile
from TaskGen import feature, before
import Task
import os

# this is a clever little thing
# given a list of nodes, build or source
# construct a tar file containing them
# rooted in the parameter root =, specified in the task generator
# and renaming the names of the files according to a rename(x) function passed to the task generator as well
# if a build node's result of rename() has the same name as a source node, the build node will take precedence
# for as long as the build node appears later than the source node (this is an implementation detail of waf we are relying on)
def tar_up(task):
	tgt = task.outputs[0].bldpath(task.env)
	if os.path.exists(tgt): os.unlink(tgt)
	if tgt.lower().endswith(".bz2"): z = tarfile.open(tgt,"w:bz2")
	elif tgt.lower().endswith(".gz"): z = tarfile.open(tgt,"w:gz")
	elif tgt.lower().endswith(".tgz"): z = tarfile.open(tgt,"w:gz")
	else: z = tarfile.open(tgt,"w")
	fileset = {}
	for inp in task.inputs:
		src = inp.srcpath(task.env)
		if src.startswith(".."):
			srcname = Utils.relpath(src,os.path.join("..",".")) # file in source dir
		else:
			srcname = Utils.relpath(src,os.path.join(task.env.variant(),".")) # file in artifacts dir
		if task.generator.rename: srcname = task.generator.rename(srcname)
		for dummy in task.generator.root.split("/"):
			splittedname = srcname.split("/")
			srcname = "/".join(splittedname[1:])
		fileset[srcname] = src
	for srcname,src in fileset.items():
		ti = tarfile.TarInfo(srcname)
		ti.mode = 0755
		ti.size = os.path.getsize(src)
		f = file(src)
		z.addfile(ti,fileobj=f)
		f.close()
	z.close()
	if task.chmod: os.chmod(tgt,task.chmod)
	return 0

def apply_tar(self):
	Utils.def_attrs(self,fun=tar_up)
	self.default_install_path=0
	lst=self.to_list(self.source)
	self.meths.remove('apply_core')
	self.dict=getattr(self,'dict',{})
	out = self.path.find_or_declare(self.target)
	ins = []
	for x in Utils.to_list(self.source):
		node = self.path.find_resource(x)
		if not node:raise Utils.WafError('cannot find input file %s for processing'%x)
		ins.append(node)
	tsk=self.create_task('tar',ins,out)
	tsk.fun=self.fun
	tsk.dict=self.dict
	tsk.install_path=self.install_path
	tsk.chmod=self.chmod
	if not tsk.env:
		tsk.debug()
		raise Utils.WafError('task without an environment')

Task.task_type_from_func('tar',func=tar_up)
feature('tar')(apply_tar)
before('apply_core')(apply_tar)
