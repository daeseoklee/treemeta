from metatree_core import *
from glob import glob 
from os.path import join,pardir,abspath,isdir,isfile

def is_prefix_of(s1,s2):
  return len(s1)<=len(s2) and s2[:len(s1)]==s1

class ExplorerState:
  def __init__(self,choicestate:ChoiceState):
    self.state=choicestate.state
    self.choicestate=choicestate
    self.rootdirname=self.state.rootdirname
    self.currentdirseq:List[str]=[]
    self.currentdirname=self.rootdirname
  def at_the_root(self):
    return self.currentdirseq==[]
  def get_pathstr(self):
    if len(self.currentdirseq)>3:
      return join('...',*self.currentdirseq[-3:])
    else:
      return join('root',*self.currentdirseq)
  def get_entries(self):
    matched_dirs=[]
    unmatched_dirs=[] 
    unregistered_dirnames=[]
    matched_files=[]
    unmatched_files=[] 
    unregistered_filenames=[]
    for path in glob(join(self.currentdirname,'*')):
      if not (isdir(path) or isfile(path)):
        pass
      elif isdir(path):
        if not path in self.state.registered_dirs:
          unregistered_dirnames.append(path)
          continue
        dir=self.state.registered_dirs[path]
        result=self.choicestate.compatible_with(dir.metadata)
        if result.ok:
          matched_dirs.append(dir)
        else:
          unmatched_dirs.append(dir)
      else:
        if not path in self.state.registered_files:
          unregistered_filenames.append(path)
          continue
        file=self.state.registered_files[path]
        result=self.choicestate.compatible_with(file.metadata)
        if result.ok:
          matched_files.append(file)
        else:
          unmatched_files.append(file)
    return matched_dirs,unmatched_dirs,unregistered_dirnames,matched_files,unmatched_files,unregistered_filenames

  def enter_dir(self,basename):
    globbed=join(self.currentdirname,basename)
    assert glob(globbed)
    assert isdir(globbed[0]) 
    self.currentdirseq.append(basename)
    self.currentdirname=join(self.currentdirname,basename)
    
  def exit_currentdir(self):
    assert self.currentdirseq!=[] 
    self.currentdirseq.pop(-1)
    self.currentdirname=abspath(join(self.currentdirname,pardir))
  