from typing import List,Tuple,Dict
from enum import Enum
import csv
from glob import glob
from os.path import join,abspath,pardir,isdir,isfile,basename


class Item: 
  def __init__(self,itemtype:str,is_root:bool,parent,registered_children,path:str,metadata:Dict[str,int]):
    assert itemtype in ['dir','file']
    self.itemtype=itemtype
    self.is_root=is_root
    self.parent=parent
    self.registered_children=registered_children
    self.path=path 
    self.metadata=metadata

class Ok():
  def __init__(self,ok:bool,conflict:str=None):
    assert not (ok==False and conflict==None)
    self.ok=ok
    self.conflict=conflict

class TreeNode:
  def __init__(self,id:str,name:str,allow_any:bool,is_multiple_choice:bool,is_optionnode:bool):
    if is_multiple_choice:
      assert len(options)==1 #'multiple choice' is simulated as a single '{multiple choice}' option with several y/n-subnodes
    self.id=id
    self.name=name #This is the displayed name
    self.options:List[Option]=[]
    self.allow_any=allow_any
    self.is_multiple_choice=is_multiple_choice
    self.is_optionnode=is_optionnode 
    self.parent:TreeNode #==self if self is a root 
  def is_descendant_of(self,other):
    if self==other:
      return True
    if self==self.parent:
      return False 
    return self.parent.is_descendant_of(other)
  def _get_id_node_pairs(self):
    id_node_pairs=[(self.id,self)]
    for option in self.options:
      for subnode in option.children:
        id_node_pairs+=subnode._get_id_node_pairs()
    return id_node_pairs
  def _compatible_eachother_under(self,metadata1:Dict[str,int],metadata2:Dict[str,int]):
    if (not self.id in metadata1) or (metadata1[self.id]==0) or (not self.id in metadata2) or (metadata2[self.id]==0):
      return Ok(True)
    n=metadata1[self.id]
    if metadata2[self.id]!=n:
      return Ok(False,conflict=self.id)
    option=self.options[n-1]
    for subnode in option.children:
      result=subnode._compatible_eachother_under(metadata1,metadata2)
      if not result.ok:
        return result
    return Ok(True)

  def _general_than_under(self,metadata1:Dict[str,int],metadata2:Dict[str,int]):
    if (not self.id in metadata1) or (metadata1[self.id]==0):
      return Ok(True) 
    if (not self.id in metadata2) or (metadata2[self.id]==0):
      return Ok(False,conflict=self.id)
    n=metadata1[self.id]
    if metadata2[self.id]!=n:
      return Ok(False,conflict=self.id)
    option=self.options[n-1]
    for subnode in option.children:
      result=subnode._general_than_under(metadata1,metadata2)
      if not result.ok:
        return result
    return Ok(True)



class Option: 
  def __init__(self,name:str,children:List[TreeNode]):
    self.name=name 
    self.children=children
    self.is_leaf=(children==[])

class MetaTree:
  def __init__(self,roots:List[TreeNode]):
    self.roots=roots
  def get_node_id_list_and_id_to_list(self):
    id_node_pairs=[]
    for root in self.roots:
      id_node_pairs+=root._get_id_node_pairs()
    return [key for key,_ in id_node_pairs],{key:val for key,val in id_node_pairs}
  def _compatible_eachother(self,metadata1:Dict[str,int],metadata2:Dict[str,int]):
    for root in self.roots:
      result=root._compatible_eachother_under(metadata1,metadata2)
      if not result.ok:
        return result
    return Ok(True)
  def _general_than(self,metadata1:Dict[str,int],metadata2:Dict[str,int]):
    for root in self.roots:
      result=root._general_than_under(metadata1,metadata2)
      if not result.ok:
        return result
    return Ok(True)

def load_metatree(filename):
  assert filename[-4:]=='.mtr'
  nodes:List[TreeNode]=[]
  roots:List[TreeNode]=[] 
  pending:Dict[str,Tuple[TreeNode,Option]]={}
  multiple_choice_pending:Dict[str,Tuple[TreeNode,Option]]={}
  current_node:TreeNode
  num_options=-1
  with open(filename,'r') as f:
    if num_options==0: #for previously delared node
      raise Exception('Node "{}" has 0 option'.format(current_node.id))
    for line in f.readlines():
      if line[0]=='=':
        if len(line)>=4 and line[:4]=="=end":
          break
        continue
      elif line[0]=='*':
        if line[1]=='*':
          allow_any=False
          if line[2]=='.':
            is_root=True
            rest=line[3:]
          else:
            is_root=False
            rest=line[2:]
        else:
          allow_any=True
          if line[1]=='.':
            is_root=True
            rest=line[2:] 
          else:
            is_root=False
            rest=line[1:]
        if '[' in rest:
          iD,name=rest.split('[')
          iD=iD.strip()
          name=name.split(']')[0].strip()
        else:
          iD=rest.strip()
          name=iD
        for ch in ['*','.']:
          if ch in iD:
            raise Exception('Illegal character "{}" in the node id "{}"'.format(ch,iD))
        if iD in [node.id for node in nodes]:
          raise Exception('Node id "{}" duplicate'.format(iD))
        if is_root and iD in pending:
          raise Exception('Node "{}" declared as a root when it was expected to be a child'.format(iD))
        if (not is_root) and (not iD in pending):
          raise Exception('Node "{}" declared as a non-root node when it was not expected to be a child. You probably have included "," in the middle of a node name.'.format(iD))
        current_node=TreeNode(iD,name,allow_any,is_multiple_choice=False,is_optionnode=(iD in multiple_choice_pending))
        nodes.append(current_node)
        if is_root:
          current_node.parent=current_node
          roots.append(current_node)
        else:
          node,option=pending[iD]
          current_node.parent=node 
          option.children.append(current_node)
          del pending[iD]
          if iD in multiple_choice_pending:
            del multiple_choice_pending[iD]
        num_options=0
      elif line[0]=='-':
        rest=line[1:]
        if '->' in rest:
          option_name,later_nodes=rest.split('->')
          option_name=option_name.strip()
          later_node_ids=[later_node_id.strip() for later_node_id in later_nodes.split(',')]
        else:
          option_name=rest.strip()
          later_node_ids=[]
        if option_name in [option.name for option in current_node.options]:
          raise Exception('Option duplicate in the node "{}"'.format(current_node.id))
        for later_node_id in later_node_ids:
          for ch in ['*','.']:
            if ch in iD:
              raise Exception('Illegal character "{}" in the new node id "{}" in the node "{}" option "{}"'.format(ch,iD,current_node.id,option_name))
          if later_node_id in pending:
            origin_node,origin_option=pending[later_node_id]
            raise Exception('Pending node name "{}" duplicate: from node "{}" option "{}" and node "{}" option "{}"'.format(later_node_id,origin_node.id,origin_option.name,current_node.id,option_name))
          if later_node_id in [node.id for node in nodes]:
            raise Exception('Pending node name duplicate in the node "{}" option "{}" for "{}"'.format(current_node.id,option_name,later_node_id))
        for i in range(len(later_node_ids)):
          for j in range(len(later_node_ids)):
            if i!=j and later_node_ids[i]==later_node_ids[j]:
              raise Exception('Pending node names duplicate in the node "{}" option "{}"'.format(current_node.id,option_name))
        if current_node.is_optionnode:
          if num_options==0 and option_name!='y':
            raise Exception('First option name not "y" in the optionnode "{}"'.format(current_node.id))
          if num_options==1 and option_name!='n':
            raise Exception('Second option name not "n" in the optionnode "{}"'.format(current_node.id))
          if num_options>=2:
            raise Exception('More than 2 options in the optionnode "{}"'.format(current_node.id))
        if '{' in option_name:
          option_keywords=option_name[option_name.find('{')+1:option_name.find('}')].split(',')
          option_keywords=[option_keyword.strip() for option_keyword in option_keywords]
          for option_keyword in option_keywords:
            if not option_keyword in ['multiple choice']:
              raise Exception('Undefined option keyword "{}" in the {}th option of the node "{}"'.format(option_keyword,1+num_options,current_node.id))
          if 'multiple choice' in option_keywords:
            if num_options!=0:
              raise Exception('Option keyword "multiple choice" used in the node "{}", which has more than one options'.format(current_node.id))
            current_node.is_multiple_choice=True
        current_node.options.append(Option(option_name,children=[]))
        for later_node_id in later_node_ids:
          pending[later_node_id]=current_node,current_node.options[-1] 
          if current_node.is_multiple_choice:
            multiple_choice_pending[later_node_id]=current_node,current_node.options[-1]
        num_options+=1
      elif line.strip()=='':
        continue
      else:
        raise Exception('illegal beginning of a line')
  for pending_node_id in pending:
    if not pending_node_id in multiple_choice_pending:
      node,option=pending[pending_node_id]
      raise Exception('Non-multiple-choice pending node "{}" came from the node "{}" option "{}" not declared'.format(pending_node_id,node.id,option.name))
  for pending_node_id in multiple_choice_pending:
    node,option=multiple_choice_pending[pending_node_id]
    y_option=Option('y',children=[])
    n_option=Option('n',children=[])
    new_node=TreeNode(id=pending_node_id,name=pending_node_id,allow_any=True,is_multiple_choice=False,is_optionnode=True)
    new_node.parent=node
    new_node.options=[y_option,n_option]
    option.children.append(new_node)
    nodes.append(new_node)
  return MetaTree(roots=roots)
          

class Decision:
  def __init__(self,name,base:TreeNode,seq:List[Tuple[TreeNode,int]],is_favorite:bool):
    assert base==seq[0][0]
    self.name=name 
    self.base=base
    self.seq=seq
    self.is_favorite=is_favorite
  def __str__(self):
    if self.is_favorite:
      return '<favorite decision-{}>'.format(self.name)
    if self.base.is_multiple_choice:
      return '<multiple choice decision-{}>'.format(self.base.name)
    return '<single decision-{}:{}'.format(self.seq[0][0].name,self.seq[0][1])
def _load_favorites(id_to_node:Dict[str,TreeNode],filename:str):
  assert len(filename)>=4 and filename[-4:]=='.csv'
  favorites={}
  with open(filename,'r',newline='') as f:
    reader=csv.reader(f,delimiter=',')
    for i,row in enumerate(reader):
      if i==0:
        for iD in row[1:]:
          assert iD in id_to_node
        node_id_list=row[1:]
        continue 
      name,baseid=row[0].split('@',1)
      restrow=row[1:]
      assert baseid in id_to_node
      seq=[(id_to_node[node_id_list[j]],int(restrow[j])) for j in range(len(restrow)) if restrow[j]!='']
      basenode=id_to_node[baseid]
      decision=Decision(name,basenode,seq,is_favorite=True)
      if basenode in favorites:
        favorites[basenode].append(decision)
      else:
        favorites[basenode]=[decision]
  return favorites
      
def _save_favorites(node_id_list:List[str],favorites:Dict[TreeNode,List[Decision]],filename:str):
  with open(filename,'w',newline='') as f:
    writer=csv.writer(f,delimiter=',')
    writer.writerow(["node"]+node_id_list)
    for basenode in favorites:
      favorite_list=favorites[basenode]
      for favorite in favorite_list:
        node_id_to_n={node.id:n for node,n in favorite.seq}
        key='{}@{}'.format(favorite.name,basenode.id)
        row=[key]
        for node_id in node_id_list:
          if node_id in node_id_to_n:
            row.append(str(node_id_to_n[node_id]))
          else:
            row.append('')
        writer.writerow(row)
    

class ChoiceState:
  def __init__(self,metatree:MetaTree,favorites:Dict[TreeNode,List[Decision]],state):
    self.metatree=metatree
    self.favorites:Dict[TreeNOde,List[Decision]]=favorites
    self.state=state

    self.decided:List[Decision]=[] 
    self.to_decide:List[TreeNode]=[root for root in metatree.roots]
    self.partial_metadata:Dict[str,int]={}
    self.active_favorites:Dict[TreeNode,List[Decision]] #everything here is a subset of self.favorites.(not copied but pulled directly)
    self.update_active_favorites()

    self.chosenlists:Dict[TreeNode,List[int]]={}
    self.init_init_chosenlists()
    
  def init_init_chosenlists(self):
    for node in self.to_decide:
      if node.is_multiple_choice:
        self.init_chosenlists(node)

  def init_chosenlists(self,node:TreeNode):
    assert node.is_multiple_choice 
    assert len(node.options)==1
    assert not node in self.chosenlists
    subnodes=node.options[0].children
    chosenlist=[0 if subnode.allow_any else 1 for subnode in subnodes]
    self.chosenlists[node]=chosenlist 

  def update_active_favorites(self):
    self.active_favorites={}
    for node in self.to_decide:
      if node in self.favorites:
        self.active_favorites[node]=self.favorites[node]

  def _decide(self,node:TreeNode,n:int): 
    #do the things except updating self.decided, updating active_favorites
    assert node in self.to_decide 
    assert 0<=n and n<=len(node.options)
    self.to_decide.remove(node)
    self.partial_metadata[node.id]=n
    if n!=0: 
      option=node.options[n-1]
      for subnode in option.children:
        self.to_decide.append(subnode)
        if subnode.is_multiple_choice:
          self.init_chosenlists(subnode)
    return 0
      
  def decide(self,node:TreeNode,n:int): 
    #node=self.to_decide[i]
    assert node in self.to_decide

    assert 0<=n and n<=len(node.options)
    assert not node.is_multiple_choice
    decision=Decision('',node,[(node,n)],False)
    self.decided.append(decision)
    self._decide(node,n)
    self.update_active_favorites()

  def decide_multiple_choice(self,node:TreeNode):
    #node=self.to_decide[i]
    assert node in self.to_decide

    assert node.is_multiple_choice
    assert len(node.options)==1
    chosenlist=self.chosenlists[node]
    subnodes=node.options[0].children 
    seq=[(node,1)]+[(subnode,chosenlist[j]) for j,subnode in enumerate(subnodes)]
    for subnode,n in seq:
      self._decide(subnode,n)
    del self.chosenlists[node]
    decision=Decision('',node,seq,False)
    self.decided.append(decision)
    self.update_active_favorites()
      
  def revert(self,decision):

    basenode=decision.base
    j=self.decided.index(decision)

    while j<len(self.decided):
      decision=self.decided[j]
      if decision.base.is_descendant_of(basenode):
        self.decided.pop(j)
        for node,_ in decision.seq:
          assert node.id in self.partial_metadata
          del self.partial_metadata[node.id]
      else:
        j+=1
    j=0
    while j<len(self.to_decide):
      node=self.to_decide[j]
      if node.is_descendant_of(basenode):
        self.to_decide.pop(j)
        if node.is_multiple_choice:
          assert node in self.chosenlists
          del self.chosenlists[node]
      else:
        j+=1


    self.to_decide.append(basenode)
    if basenode.is_multiple_choice:
      self.init_chosenlists(basenode)
    self.update_active_favorites()

  def apply_favorite(self,node,favorite):
    #favorite=self.favorites[node][i]

    assert favorite in self.favorites[node]

    assert node in self.to_decide 
    for node,n in favorite.seq:
      self._decide(node,n)
      if node.is_multiple_choice:
        assert node in self.chosenlists
        del self.chosenlists[node]
    self.decided.append(favorite)
    self.update_active_favorites()

  def add_current_as_favorite(self,basenode,name):
    assert basenode in [decision.base for decision in self.decided]
    assert (not basenode in self.favorites) or (not name in [favorite.name for favorite in self.favorites[basenode]])
    for ch in ['@']:
      if ch in name:
        raise Exception('Illegal character "{}" in the favorite name "{}"'.format(ch,name))
    i=0
    while not self.decided[i].base==basenode: 
      i+=1
    seq=[]
    for j in range(i,len(self.decided)):
      if self.decided[j].base.is_descendant_of(basenode):
        decision=self.decided[j]
        seq+=decision.seq
    favorite=Decision(name,basenode,seq,True)
    if not basenode in self.favorites:
      self.favorites[basenode]=[] 
    self.favorites[basenode].append(favorite)
    self.update_active_favorites()  

  def remove_favorite(self,node,favorite):
    #assert 0<=i and i<=len(self.favorites[node])-1

    assert node in self.favorites
    assert favorite in self.favorites[node]

    self.favorites[node].remove(favorite)
    if self.favorites[node]==[]:
      del self.favorites[node]
    self.update_active_favorites()
  def compatible_with(self,metadata):
    return self.metatree._compatible_eachother(self.partial_metadata,metadata)
  def revert_all(self):
    while self.decided!=[]:
      self.revert(self.decided[0])

  def fit_metadata(self,metadata):
    for node_id in metadata:
      assert node_id in self.state.id_to_node
    def agree_on(node_id,n):
      return (node_id in metadata) and metadata[node_id]==n
    def use_favorite(favorite):
      favorite:Decision
      for node,n in favorite.seq:
        if not agree_on(node.id,n):
          return False
      return True 
    
    self.revert_all()

    while True:
      done=False
      for node in self.active_favorites:
        for favorite in self.active_favorites[node]:
          if use_favorite(favorite):
            self.apply_favorite(node,favorite)
            done=True
            break
        if done:
          break
      if done:
        continue 
      for node in self.to_decide:
        if node.id in metadata:
          if not node.is_multiple_choice:
            n=metadata[node.id]
            self.decide(node,n)
          else:
            assert metadata[node.id]==1
            option=node.options[0]
            for i,subnode in enumerate(option.children):
              subnode:TreeNode
              n=metadata[subnode.id] 
              self.chosenlists[node][i]=n
            self.decide_multiple_choice(node)
          done=True
          break
      if done:
        continue
      break
      


class MetadataEditException(Exception):
  def __init__(self,path,problem,conflict_path=None,conflict_node_id=None,this_n=0,other_n=0):
    self.path=path 
    self.problem=problem #'child_conflict','parent_conflict' 
    self.conflict_path=conflict_path
    self.conflict_node_id=conflict_node_id
    self.this_n=this_n
    self.other_n=other_n 
    super().__init__()



class State:
  def __init__(self,rootdirname,metatree_filename,favorites_filename,metadata_filename):
    self.metatree_filename=metatree_filename
    self.favorites_filename=favorites_filename
    self.metadata_filename=metadata_filename
    
    self.rootdirname=rootdirname
    self.metatree=load_metatree(self.metatree_filename)

    self.id_to_node:Dict[str,TreeNode]
    self.node_id_list:List[str]
    self.node_id_list,self.id_to_node=self.metatree.get_node_id_list_and_id_to_list()

    self.favorites=self.load_favorites() #keep this order within __init__ but you can freely call load_favorites in other places
    self.rootdir,self.registered_dirs,self.registered_files=self.load_metadata() #keep this order within __init__ but you can freely call load_metadata in other places



  def make_choicestate(self):
    return ChoiceState(self.metatree,self.favorites,state=self)

  def compatible_eachother(self,item1:Item,item2:Item):
    return self.metatree._compatible_eachother(item1.metadata,item2.metadata)
  def general_than(self,item1:Item,item2:Item):
    return self.metatree._general_than(item1.metadata,item2.metadata)
  def save_favorites(self):
    _save_favorites(self.node_id_list,self.favorites,self.favorites_filename)
  def load_favorites(self):
    if glob(self.favorites_filename)==[]:
      return {}
    return _load_favorites(self.id_to_node,self.favorites_filename)
  def load_metadata(self):
    if not glob(self.metadata_filename):
      return None,{},{}
    rootdir=None 
    registered_dirs={}
    registered_files={} 
    #dirname_to_item={}
    this_file_node_id_list=[] 
    with open(self.metadata_filename,'r') as f:
      reader=csv.reader(f,delimiter=',')
      this_file_node_id_list=next(reader)[2:]
      for node_id in this_file_node_id_list:
        if not node_id in self.id_to_node:
          raise Exception('no node_id "{}" in the current metatree'.format(node_id))
      for line in reader:
        path=line[0]
        file_or_dir=line[1]
        metadata={}
        for i,n in enumerate(line[2:]):
          if n!='':
            node_id=this_file_node_id_list[i]
            metadata[node_id]=int(n)
        if file_or_dir=='dir':
          if path==self.rootdirname:
            item=Item('dir',is_root=True,parent=None,registered_children=[],path=path,metadata=metadata)
            rootdir=item 
          else:
            parent_dirname=abspath(join(path,pardir))
            parent=registered_dirs[parent_dirname]
            item=Item('dir',is_root=False,parent=parent,registered_children=[],path=path,metadata=metadata)
            parent.registered_children.append(item) 
          registered_dirs[path]=item
        else:
          parent_dirname=abspath(join(path,pardir))
          parent=registered_dirs[parent_dirname]
          item=Item('file',is_root=False,parent=parent,registered_children=None,path=path,metadata=metadata)
          parent.registered_children.append(item)
          registered_files[path]=item 
    if rootdir==None:
      raise Exception('no rootdir in the favorites file')
    for dirname in registered_dirs:
      dir=registered_dirs[dirname]
      if not dir.is_root:
        assert dir.parent.path in registered_dirs
        assert self.general_than(dir.parent,dir).ok
    for filename in registered_files:
      file=registered_files[filename]
      assert file.parent.path in registered_dirs
      assert self.general_than(file.parent,file).ok
    return rootdir,registered_dirs,registered_files

    
  def save_metadata(self):
    dirname_to_item={}
    with open(self.metadata_filename,'w',newline='') as f:
      writer=csv.writer(f,delimiter=',')
      writer.writerow(['item','file/dir']+self.node_id_list)
      for dirname in self.registered_dirs:
        dir=self.registered_dirs[dirname]
        assert (dir.is_root or dir.parent.path in dirname_to_item)
        row=[dir.path,'dir']
        for node_id in dir.metadata:
          assert node_id in self.id_to_node
        for node_id in self.node_id_list:
          if node_id in dir.metadata:
            row.append(str(dir.metadata[node_id]))
          else:
            row.append('')
        writer.writerow(row)
        dirname_to_item[dir.path]=dir 
      assert self.rootdirname in dirname_to_item 
      for filename in self.registered_files:
        file=self.registered_files[filename]
        for node_id in file.metadata:
          assert node_id in self.id_to_node
        row=[file.path,'file']
        for node_id in self.node_id_list:
          if node_id in file.metadata:
            row.append(str(file.metadata[node_id]))
          else:
            row.append('')
        writer.writerow(row)
      
  def assert_may_unregister_path(self,path):
    globbed=glob(path)
    if not globbed:
      raise Exception('Path does not exist: {}'.format(path))
    if len(glob(path))>1:
      raise Exception('More than one match: {}'.format(path))
    path=globbed[0]
    if isdir(path):
      if not path in self.registered_dirs:
        raise Exception('Directory not registered yet: {}'.format(path))
      dir=self.registered_dirs[path]
      if dir.registered_children!=[]:
        child=dir.registered_children[0]
        raise Exception('There exists a registered children {}: {}'.format(child.path,path))
    else:
      if not path in self.registered_files:
        raise Exception('File not registered yet: {}'.format(path))
    pass

  def unregister_path(self,path):
    self.assert_may_unregister_path(path)
    path=glob(path)[0]
    if isdir(path):
      dir=self.registered_dirs[path]
      if not dir.is_root:
        dir.parent.registered_children.remove(dir)
      del self.registered_dirs[path]
    else:
      file=self.registered_files[path]
      file.parent.registered_children.remove(file)
      del self.registered_files[path]

  def assert_may_register_path(self,path,metadata=None):
    #if metadata=None, it checks the conditions other than those for metadata
    globbed=glob(path)
    if not globbed:
      raise Exception('Path does not exist: {}'.format(path))
    if len(glob(path))>1:
      raise Exception('More than one match: {}'.format(path))
    path=globbed[0]
    if not (isdir(path) or isfile(path)):
      raise Exception('neither dir nor file')
    if isdir(path):
      if path in self.registered_dirs:
        raise Exception('Directory already registered: {}'.format(path))
      if path!=self.rootdirname:
        parent_dirname=abspath(join(path,pardir))
        if not parent_dirname in self.registered_dirs:
          raise Exception('Parent directory of the directory not registered: {}'.format(path))
        if metadata!=None:
          parent=self.registered_dirs[parent_dirname]
          result=self.metatree._general_than(parent.metadata,metadata)
          if not result.ok:
            conflict_id=result.conflict
            this_n=0 if (not conflict_id in metadata) else metadata[conflict_id]
            other_n=0 if (not conflict_id in parent.metadata) else parent.metadata[conflict_id]
            raise MetadataEditException(path,'parent_conflict',conflict_path=parent.path,conflict_node_id=result.conflict,this_n=this_n,other_n=other_n)
    else:
      if path in self.registered_files:
        raise Exception('File already registered: {}'.format(path))
      parent_dirname=abspath(join(path,pardir))
      if not parent_dirname in self.registered_dirs:
        raise Exception('Parent directory of the file not registered: {}'.format(path))
  def register_path(self,path,metadata):
    self.assert_may_register_path(path,metadata)
    globbed=glob(path)
    path=globbed[0]
    if isdir(path):
      if path==self.rootdirname:
        self.registered_dirs[path]=Item('dir',is_root=True,parent=None,registered_children=[],path=path,metadata=metadata)
      else:
        parent_dirname=abspath(join(path,pardir))
        parent=self.registered_dirs[parent_dirname]
        item=Item('dir',is_root=False,parent=parent,registered_children=[],path=path,metadata=metadata)
        parent.registered_children.append(item)
        self.registered_dirs[path]=item
    else:
      parent_dirname=abspath(join(path,pardir))
      parent=self.registered_dirs[parent_dirname]
      item=Item('file',is_root=False,parent=parent,registered_children=None,path=path,metadata=metadata)
      parent.registered_children.append(item)
      self.registered_files[path]=item
  def assert_may_edit_path_metadata(self,path,metadata):
    globbed=glob(path)
    if not globbed:
      raise Exception('path does not exist: {}'.format(path))
    if len(globbed)>1:
      raise Exception('More than one matches: {}'.format(path))
    path=globbed[0]
    if not (isdir(path) or isfile(path)):
      raise Exception('neither dir nor file')
    if isdir(path): 
      if not path in self.registered_dirs:
        raise Exception('directory not registered yet: {}'.format(path))
      dir=self.registered_dirs[path]
      if path!=self.rootdirname:
        result=self.metatree._general_than(dir.parent.metadata,metadata)
        if not result.ok:
          id=result.conflict
          this_n=0 if (not id in metadata) else metadata[id]
          other_n=0 if (not id in dir.parent.metadata) else dir.parent.metadata[id]
          raise MetadataEditException(path,'parent_conflict',conflict_path=dir.parent.path,conflict_node_id=id,this_n=this_n,other_n=other_n)

      for child in dir.registered_children:
        result=self.metatree._general_than(metadata,child.metadata)
        if not result.ok:
          id=result.conflict
          this_n=0 if (not id in metadata) else metadata[id]
          other_n=0 if (not id in child.metadata) else child.metadata[id]
          raise MetadataEditException(path,'child_conflict',conflict_path=child.path,conflict_node_id=id,this_n=this_n,other_n=other_n)

    else:
      if not path in self.registered_files: 
        raise Exception('file not registered yet: {}'.format(path))
      file=self.registered_files[path]
      if not self.metatree._general_than(file.parent.metadata,metadata).ok:
        raise Exception('The parent is not more general: {}'.format(path))
      file.metadata=metadata

  def edit_path_metadata(self,path,metadata):
    self.assert_may_edit_path_metadata(path,metadata)
    if isdir(path):
      dir=self.registered_dirs[path]
      dir.metadata=metadata
    else:
      file=self.registered_files[path]
      file.metadata=metadata
  

      
      
    




class StateManager():
  def __init__(self,config_filepattern):
    self.default_rootdir_idx=0
    self.info=[]
    self.load_config(config_filepattern)
  def load_default_state(self):
    return self.load_state(self.default_rootdir_idx)
  def load_state(self,i):
    rootdir,metatree_filename,favorites_filename,metadata_filename=self.info[i]
    return State(rootdir,metatree_filename,favorites_filename,metadata_filename)
  def load_config(self,config_filepattern):
    globbed=glob(config_filepattern)
    if not globbed:
      raise Exception('no file match: {}'.format(config_filepattern))
    elif len(globbed)>1:
      raise Exception('more than one file that match: {}'.format(config_filepattern))
    config_filename=globbed[0]
    with open(config_filename,'r') as f:
      current_rootdir_idx=None
      rootdirs=[]
      mode=None
      metatree_filename,favorites_filename,metadata_filename=None,None,None
      for i,rawline in enumerate(f.readlines()):
        line=rawline.strip()
        if i==0 and line!='#treemeta config file':
          raise Exception('First line not "#treemeta config file"')
        elif i==0:
          continue 
        elif line=='':
          continue 
        elif line[0]=='<':
          if len(line)==1:
            raise Exception('invalid line "<" in the config file')
          elif line[1]!='<':
            if mode!=None:
              raise Exception('field <{}> not filled or not closed'.format(mode))
            mode=line[1:line.find('>')].strip()
          else: #line[:2]=='<<'
            if mode!=None:
              raise Exception('field <{}> not filled'.format(mode))
            current_rootdir_idx=int(line[2:line.find('>>')])-1
            if current_rootdir_idx<0 or current_rootdir_idx>len(rootdirs)-1:
              raise Exception('invalid root index "<<{}>>"'.format(current_rootdir_idx+1))
        elif line=='///':
          if current_rootdir_idx==None:
            raise Exception('"///" at a wrong place: line "{}"'.format(1+i))
          if metatree_filename==None:
            raise Exception('metatree filename not set for {}-th root'.format(1+current_rootdir_idx))
          if favorites_filename==None:
            raise Exception('favorites filename not set for {}-th root'.format(1+current_rootdir_idx))
          if metadata_filename==None:
            raise Exception('metadata filename not set for {}-th root'.format(1+current_rootdir_idx))
          assert len(self.info)==current_rootdir_idx 
          metatree_filename=abspath(join(config_filename,pardir,metatree_filename))
          favorites_filename=abspath(join(config_filename,pardir,favorites_filename))
          metadata_filename=abspath(join(config_filename,pardir,metadata_filename))
          self.info.append((rootdirs[current_rootdir_idx],metatree_filename,favorites_filename,metadata_filename))
          current_rootdir_idx=None
          metatree_filename,favorites_filename,metadata_filename=None,None,None
          
        elif mode==None:
          raise Exception('invalid format at line "{}"'.format(1+i))
        elif mode=='default rootdir':  
          self.default_rootdir_idx=int(line)-1
          mode=None 
        elif mode=='rootdirs':
          if line=='//':
            mode=None
            continue 
          if not '.' in line:
            raise Exception('invalid rootdir at line "{}"'.format(1+i))
          dot_idx=line.find('.')
          rootdir_idx=int(line[:dot_idx].strip())-1
          rootdir=line[1+dot_idx:].strip()
          if len(rootdirs)!=rootdir_idx:
            raise Exception('wrong rootdir index at line "{}"'.format(rootdir_idx))
          rootdirs.append(rootdir)
        elif mode=='metatree file':
          metatree_filename=line 
          mode=None
        elif mode=='favorites file':
          favorites_filename=line
          mode=None
        elif mode=='metadata file':
          metadata_filename=line
          mode=None
        
        
      if self.default_rootdir_idx<0 or self.default_rootdir_idx>len(rootdirs):
        raise Exception('invalid default rootdir index')
        
        
        

def main():
  sm=StateManager('config/config.txt')
  state=sm.load_default_state()
if __name__=='__main__':
  main()