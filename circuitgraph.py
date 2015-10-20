# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 22:31:02 2015
@author: litao
@e-mail:litaotju@qq.com
address:Tianjin University
"""

import re
import networkx as nx
import matplotlib.pyplot as plt
import class_circuit as cc
from sgraph import s_graph
from exception import *

class CircuitGraph(nx.DiGraph):
    '''
       This class is a sonclass of nx.DiGraph and construct with a m_list[]
       Property new added :
           self.include_pipo self.vertex_set,self.edge_set
       Node attr :
           node_type ,which is a cellref or the port_type if node is pipo
           name , which is the module.name or port.port_name
       Edge attr :
           connection,which is the string of wire signal name which connect prim
           port_pair, which records the port instance pair
    '''

    def __init__(self, m_list, include_pipo = True):
        '''Para:
                m_list : cc.circuit_module list, produced by netlist_parser
                include_pipo : indict that if the graph produced will have pipo vertex and edge
        '''
        nx.DiGraph.__init__(self)
        self.name = m_list[0].name
        self.m_list = m_list
        self.include_pipo = include_pipo
        self.__add_vertex_from_m_list()
        self.__get_edge_from_prim_list()
        self.cloud_reg_graph = None
        self.s_graph = None
        print "Note: circuit_graph() build successfully"

    def __add_vertex_from_m_list(self):

        print "Process: searching the vertex of graph from m_list..."
        pipo_vertex_list=[]
        prim_vertex_list=[]
        vertex_set=[]
        ###########################################################################
        #vertex
        prim_vertex_list = self.m_list[1:]
        for eachPrim in self.m_list[1:]:
            #now we cannot handle the graph construction problem with concering DSP
            #because, in hardware fault injection emulaiton process, when signal passing
            #DSP, we cannot compute the signal correctly
            assert eachPrim.cellref not in ['DSP48','DSP48E1','DSP48E'],\
                "CircuitGraph Error: %s found %s " % (eachPrim.cellref, eachPrim.name)
            self.add_node(eachPrim, node_type = eachPrim.cellref, name = eachPrim.name)
        pipo_vertex_list = self.m_list[0].port_list
        if self.include_pipo:
            for eachPipo in pipo_vertex_list:
                self.add_node(eachPipo, node_type = eachPipo.port_type, name = eachPipo.name)
        vertex_set = prim_vertex_list + pipo_vertex_list

        self.prim_vertex_list = prim_vertex_list
        self.pipo_vertex_list = pipo_vertex_list
        self.vertex_set = vertex_set
        ###########################################################################
        #edge
        #edge_set的每一个元素是 一个([],[],{})类型的变量,
        #第一个列表存储prim,第二个存储port,第三个存储连接信号
        #---------------------------pipo edge ------------------------------------
        #if include_pipo:
        #    print "    Process: searching PI and PO edges..."
        #    for eachPrim in prim_vertex_list:
        #        for eachPort in eachPrim.port_list:
        #            for eachPPort in pipo_vertex_list:
        #                cnt_flag=False
        #                #信号名称等于端口名称,可能prim port的信号是pipo的某一bit
        #                if isinstance(eachPort.port_assign, cc.signal) and \
        #                        eachPort.port_assign.name == eachPPort.port_name:
        #                    connection = eachPort.port_assign.name
        #                    cnt_flag = True
        #                # 这一部分用于多位端口的连接
        ##                elif isinstance(eachPort.port_assign,cc.joint_signal):
        ##                    for eachSubsignal in eachPort.port_assign.sub_signal_list:
        ##                        if eachSubsignal.name==eachPPort.port_name:
        ##                            cnt_flag=True
        ##                            break
        ##                        else:
        ##                            continue
        #                if cnt_flag:
        #                    if eachPPort.port_type=='input':
        #                        assert eachPort.port_type in ['input', 'clock'],\
        #                            ("%s %s  port:%s, port_type:%s"\
        #                            % (eachPrim.cellref, eachPrim.name, \
        #                               eachPort.port_name, eachPort.port_type))
        #                        pi_edge_list.append([[eachPPort,eachPrim], [eachPPort,eachPort], connection])
        #                    else:
        #                        ##只有输prim 的输出端口 才能连接到po port上。否则只是PO的反馈，一定在prim_edge中存在
        #                        if eachPort.port_type=='output':
        #                            po_edge_list.append([[eachPrim,eachPPort], [eachPort,eachPPort], connection])
        
        #print "    Process: searching Prim edges..."
        #self.fd_loop = []
        ##---------------------------prim edge --------------------------------------------
        #for eachPrim in prim_vertex_list:
        #    for eachPrim2 in prim_vertex_list:
        #        # 存在prim与自身的连接
        #        p_set = set(eachPrim.port_assign_list)
        #        p_set2 = set(eachPrim2.port_assign_list)
        #        if not p_set.intersection(p_set2):
        #            continue
        #        for eachPort in eachPrim.port_list:
        #            for eachPort2 in eachPrim2.port_list:
        #                sig1 = eachPort.port_assign.string
        #                sig2 = eachPort2.port_assign.string
        #                if sig2 == sig1 and \
        #                    eachPort2.port_type != eachPort.port_type:
        #                    if eachPrim is eachPrim2 :
        #                        assert eachPrim.m_type == 'FD' ,\
        #                        "Combinational Prim loop: %s %s" % ( eachPrim.cellref, eachPrim.name )
        #                        #print "        FD-self loop %s %s " % ( eachPrim.cellref, eachPrim.name )
        #                        self.fd_loop.append( (eachPrim , eachPort, eachPort2) )
        #                    connection = sig2
        #                    if eachPort.port_type == 'input':
        #                        tmp_edge = [[eachPrim2 ,eachPrim], [eachPort2, eachPort], connection]
        #                    else:
        #                        tmp_edge = [[eachPrim, eachPrim2], [eachPort ,eachPort2],  connection]
        #                    if tmp_edge in prim_edge_list:
        #                        continue
        #                    prim_edge_list.append(tmp_edge)

        ##--------merge all the edge-------------------------------------------------------
        #self.pi_edge_list   = pi_edge_list
        #self.po_edge_list   = po_edge_list
        #self.prim_edge_list = prim_edge_list
        #self.edge_set       = pi_edge_list + po_edge_list + prim_edge_list
        #for eachEdge in self.edge_set:
        #    self.add_edge(eachEdge[0][0], eachEdge[0][1],\
        #    connection=eachEdge[2] , port_pair=eachEdge[1])
        return None
    #------------------------------------------------------------------------------

    def __get_edge_from_prim_list(self):
        '''从prim_list当中获得边的连接的信息。
            如果self.include_pipo为真，此函数不仅将与PIPO相连接的边加入到生成的图中
            而且将为生成的CircuitGraph对象增加self.pi_edge_list和self.po_edge_list
            不论self.include_pipo为真与否，都会增加self.prim_edge_list和self.edge_set
        '''
        piname = {} #PI　instances dict keyed by name
        poname = {}
        for primary in self.pipo_vertex_list:
            if primary.port_type == 'input':
                piname[primary.name] = primary
                continue
            elif not primary.port_type == 'output':
                print "Error :found an primary port neither input nor output "
                print "       %s %s" % (primary.name,primary.port_type) 
                raise CircuitGraphError
            poname[primary.name] = primary
        pi_dict = {}  # pi_dict[wire1] = {'source':pi,'sink':[]}
        po_dict = {}  # po_dict[wire1] = {'source':(),'sink':po }
        cnt_dict = {} # cnt_dict[wire1] = {'source':(),'sink':[(prim,port),()...]}

        print "Process: searching edges from prim_vertex_list..."
        for eachPrim in self.prim_vertex_list:
            for eachPort in eachPrim.port_list:
                #assert每一个端口里面的wire都是单比特信号
                if not eachPort.port_width == 1:
                    print "Error: >1 bitwidth signal found in %s %s"\
                        % (eachPrim.name, eachPort.port_name)
                    raise CircuitGraphError
                # a bit wire is the format : .string = .name[.bit_loc]
                wire_name = eachPort.port_assign.name # 名称
                wire = eachPort.port_assign.string    # 全名 = 名称[n]
                # 如果这个信号是包含在PI名字里面
                if  piname.has_key(wire_name):
                    if not pi_dict.has_key(wire):
                        pi_dict[wire] = {'source':piname[wire_name],'sink':[]}
                    if not eachPort.port_type in ['input','clock']:
                        print "Error: PI %s connect to Prim's Non-input Port: %s %s"\
                            % (wire_name, eachPrim.name, eachPort.port_name)
                        raise CircuitGraphError
                    pi_dict[wire]['sink'].append( (eachPrim, eachPort) )
                    continue
                # 如果这个信号的名字包含在PO名字里面
                if poname.has_key(wire_name):
                    # 无论如何将PO中的信号全部加入到cnt_dict的信息中，之后将没有prim sink的那些信号进行过滤
                    if not cnt_dict.has_key(wire):
                        cnt_dict[wire] = { 'source':(),'sink':[] }
                    if eachPort.port_type == 'output':
                        cnt_dict[wire]['source'] = (eachPrim, eachPort)
                    else:
                        cnt_dict[wire]['sink'].append( (eachPrim, eachPort) )
                    # 将这个信号的连接信息加入到po_dict中
                    if eachPort.port_type == "output":
                        if not po_dict.has_key(wire):
                            po_dict[wire] = {'source':(eachPrim, eachPort),'sink':poname[wire_name]}
                        else: #有别的输出端口已经连接到这个属于po的wire上，直接报错
                            #if po_dict[wire]['source']: #如果这个PO的bit位信号，已经有source了
                            print "wire: PO %s has more than 1 source. 1st source is %s %s.2nd source is %s %s"\
                                % (wire, po_dict[wire]['source'][0].name,po_dict[wire]['source'][1].port_name,\
                                   eachPrim.cellref, eachPrim.name)
                            raise CircuitGraphError
                    #po_dict[wire]['source'] = (eachPrim, eachPort)
                    continue
                # 如果这个信号的名字既没包含在PI也没包含在PO,那只能是Prim之间的连接了
                if eachPort.port_type == 'clock':
                    assert pi_dict.has_key(eachPort.port_assign.string)
                    continue
                if not cnt_dict.has_key(wire):
                    cnt_dict[wire] = {'source':(),'sink':[] }
                if eachPort.port_type == 'output':
                    if cnt_dict[wire]['source']: #如果这个信号已经有一个source了
                        print "wire: %s has more than 1 source.1st source is %s %s .2nd source is %s %s"\
                            % (wire, cnt_dict[wire]['source'][0].name, cnt_dict[wire]['source'][1].port_name,\
                               eachPrim.cellref, eachPrim.name) 
                        raise CircuitGraphError
                    cnt_dict[wire]['source'] = (eachPrim, eachPort)
                    continue
                if eachPort.port_type == 'input':
                    cnt_dict[wire]['sink'].append( (eachPrim, eachPort) )
                    continue
                # 如果运行到这里了，说明当前这个wire什么也没有连接到
                print "Error: wire cnt to neither input nor output port. %s %s %s"\
                    % (eachPrim.name ,eachPort.name, eachPort.port_type) 
                raise CircuitGraphError
        # ------------------------------------------------------------------------
        # prim_edge的找出
        self.prim_edge_list =[]
        for eachWire, SourceSinkDict in cnt_dict.iteritems():
            source = SourceSinkDict['source']
            sinks = SourceSinkDict['sink']
            if not source:
                print "Warning: no source of signal %s " % eachWire
                # print "Error: no source of signal %s " % eachWire
                # raise CircuitGraphError
                continue
            if len(sinks) < 1 :
                # GND VCC 的输出可能不会连接到其他PRIM上，所以其sink可以为0
                if source[0].cellref in ['VCC', 'GND']:
                    continue
                #print "Waring: %s has no prim sink ,its source is %s %s %s"%\
                #    (eachWire, source[0].cellref, source[0].name, source[1].port_name)
                #continue
            for eachSink in sinks:
                self.add_edge(source[0], eachSink[0],\
                    port_pair = (source[1], eachSink[1]),\
                    connection = eachWire)
                prim_edge = [ [source[0], eachSink[0]],[source[1], eachSink[1]], eachWire ]
                self.prim_edge_list.append(prim_edge)
        self.edge_set = []

        # 如果不包含PIPO，那么现在就退出函数，不将与PIPO相连接的边加入到图中
        if not self.include_pipo:
            self.edge_set = self.prim_edge_list
            print "Note: get all edges succsfully, WARING : NO PIPO EDGES IN GRAPH"
            return None
        # ------------------------------------------------------------------------
        # pipo_edge的找出
        print "Processing: searching PIPO edges from m_list..."
        self.pi_edge_list = []
        self.po_edge_list = []
        for eachWire,piConnect in pi_dict.iteritems():
            source = piConnect['source']  # cc.port instance
            sinks = piConnect['sink']
            for eachSink in sinks:
                self.add_edge(source,eachSink[0],\
                              port_pair = (source,eachSink[1]),\
                              connection = eachWire)
                pi_edge = [ [source,eachSink[0]], [source, eachSink[1]],eachWire]
                self.pi_edge_list.append(pi_edge)
        for eachWire, poConnect in po_dict.iteritems():
            source = poConnect['source'] # a tuple (prim, port)
            sink = poConnect['sink']   #cc.port instance
            self.add_edge(source[0], sink,\
                          port_pair = (source[1], sink),\
                          connection= eachWire)
            po_edge = [ [source[0], sink], [source[1], sink], eachWire]
            self.po_edge_list.append(po_edge)
        # 将所有的Edge合并到self.edge_set属性当中
        self.edge_set = self.pi_edge_list + self.po_edge_list + self.prim_edge_list
        print "Note : get all the edges succsfully"
        return None
    #------------------------------------------------------------------------------
    def info(self, verbose = False) :
        print "----- module %s -- CircuitGraph info:----- " % self.m_list[0].name
        print nx.info(self)
        if verbose:
            print "Info :%d nodes in graph. Node Set Are:"% self.number_of_nodes()
            node_type = nx.get_node_attributes(self, 'node_type')
            name = nx.get_node_attributes(self, 'name')
            for eachNode in self.nodes_iter():
                print "    %s %s" % (node_type[eachNode], name[eachNode])

            print "Info :%d edges in graph. Edge Set Are:"% self.number_of_edges()
            connection = nx.get_edge_attributes(self, 'connection')
            port_pair = nx.get_edge_attributes(self, 'port_pair')
            for eachEdge in self.edges_iter():
                print "    (%s -> %s):(wire %s, port:%s->%s)" % \
                (eachEdge[0].name,eachEdge[1].name,connection[eachEdge]\
                ,port_pair[eachEdge][0].name,port_pair[eachEdge][1].name)
        return None
    #------------------------------------------------------------------------------
    
    def paint(self):
        ''' 给电路图，分组画出来，不同的颜色和标签标明了不同的prim '''
        label_dict={}
        fd_list  = []
        pipo_list= []
        others   = []
        for eachVertex in self.nodes_iter():
            if isinstance(eachVertex, cc.circut_module):
                label_dict[eachVertex] = eachVertex.cellref + " : " + eachVertex.name
                if eachVertex.m_type == 'FD':
                    fd_list.append(eachVertex)
                else:
                    others.append(eachVertex)
            else:
                assert isinstance(eachVertex, cc.port)
                label_dict[eachVertex] = eachVertex.port_type + \
                    " : " + eachVertex.port_name
                pipo_list.append(eachVertex)
        ps = nx.spring_layout(self)
        if self.include_pipo:
            nx.draw_networkx_nodes(self,pos=ps,nodelist=pipo_list,node_color='r')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=others,node_color='b')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=fd_list,node_color='g')
        nx.draw_networkx_edges(self,ps)
        nx.draw_networkx_labels(self,ps,labels=label_dict)
        plt.savefig("test_output\\"+self.m_list[0].name+"_original_.png")
        return None
        

    ###############################################################################
    def get_s_graph(self):
        '''
           >>>self.s_graph.copy(),根据已有的图来生成s-graph
           生成的s图完全是nx.DiGraph类的，不是自定义类，初步评估发现，用这种方法
           生成s图比 原先graph_s_graph中的只处理边集和点集更快速。所以有必要修改
           该类的定义和构造函数。
        '''
        care_type=('FD')
        ##step1
        ##无聊的初始化过程，先建一个s_graph的对象，然后直接对数据属性进行赋值
        s1=s_graph(self.include_pipo)
        s1.name=self.name
        if self.include_pipo:
            for x in self.pipo_vertex_list:
                if x.port_type=='input':
                    s1.pi_nodes.append(x)
                else:
                    s1.po_nodes.append(x)
        for fd in self.prim_vertex_list:
            if fd.m_type=='FD':
                s1.fd_nodes.append(fd)
        ##为DiGraph内核添加节点与边
        s1.add_nodes_from(self.vertex_set)
        for eachEdge in self.edge_set:
            s1.add_edge(eachEdge[0][0],eachEdge[0][1],\
                    port_pair=eachEdge[1],cnt=eachEdge[2])
        node_type_dict=nx.get_node_attributes(self,'node_type')   
        
        ##step2
        ##ignore 每一个非FD的primitive节点
        new_edge=[]
        for eachNode in self.nodes_iter():
            if node_type_dict[eachNode] not in ['input','output']:
                if eachNode.m_type not in care_type:
                    pre=[]
                    suc=[]
                    pre=s1.predecessors(eachNode)
                    suc=s1.successors(eachNode)
                    s1.remove_node(eachNode)
                    if pre and suc:
                        for eachS in pre:
                            for eachD in suc:
                                new_edge.append((eachS,eachD))
                                s1.add_edge(eachS,eachD)
        ##为新添加的边归类，
        s1.new_edges=new_edge
        self.s_graph=s1
        return s1.copy()

    def to_gexf_file(self, filename):
        '''把图写入gexf文件，不对原图做任何改变
            新图中的节点增加了id和label两个属性
        '''
        new_graph = nx.DiGraph()
        for node in self.nodes_iter():
            node_label = node.cellref if isinstance(node, cc.circut_module) else node.port_type
            node_id = '_d_'+node.name[1:] if node.name[0]=='\\' else node.name
            new_graph.add_node(node, id= node_id, label = node_label)
        for start, end, data in self.edges_iter(data=True):
            #label = data['connection']
            new_graph.add_edge(start, end)
        nx.write_gexf(new_graph, filename)

    def to_dot_file(self, filename):
        '''把图写入到dot文件中，不对原图做什么改变
            新图的节点只是字符串。
        '''
        new_graph = nx.DiGraph()
        for start, end, data  in self.edges_iter(data = True):
            port_pair = data['port_pair']
            connection = data['connection']
            edge = [start, end] # 存储边的起点和终点
            node_id =['','']    # 存储节点的名称
            node_data =[{},{}]  # 存储要打印到dot中的信息
            for i in range(2):
                # 当前节点是prim 或者是 port
                is_prim = True if isinstance(edge[i], cc.circut_module) else False
                # prim和port的数据属性不同，根据判断为生成dot节点的名称，和节点附属的['shape']数据
                node_name = '_d_'+edge[i].name[1:] if edge[i].name[0]=='\\' else edge[i].name 
                node_id[i] = edge[i].cellref+node_name if is_prim else\
                             edge[i].port_type+node_name
                # prim为box形状（盒子），port为invtriangle形状（倒三角）
                node_data[i]['shape'] = 'box' if is_prim else 'invtriangle' 
                new_graph.add_node(node_id[i],node_data[i])
            new_graph.add_edge(node_id[0], node_id[1])
        nx.write_dot(new_graph, filename)
#------------------------------------------------------------------------------
        
def get_graph_from_raw_input(fname = None):
    '''for test only'''
    import netlist_util as nu
    if not fname:
        fname = raw_input("plz enter file name:")
    info = nu.vm_parse(fname)
    m_list = info['m_list']
    print "Top module is:"
    m_list[0].__print__()
    nu.mark_the_circut(m_list)
    nu.rules_check(m_list)
    g1 = CircuitGraph(m_list, include_pipo = True)
    debug = True
    if debug:
        # 打印扇入为0的FD的信息
        fd_nodes = [fd for fd in g1.nodes_iter() if isinstance(fd, cc.circut_module) and fd.m_type=='FD']
        print "0 in-degree fd:"
        for fd in fd_nodes:
            if g1.in_degree(fd) == 0:
                fd.__print__()
    return g1
    
def __test():
    '''for test only,输入一个文件名，生成带PIPO和不带PIPO的图，
       然后将生成的图分别保存到tmp\\下的.dot文件和.gexf文件
    '''
    import netlist_util as nu
    fname = raw_input("plz enter file name:")
    info = nu.vm_parse(fname)
    m_list = info['m_list']

    nu.mark_the_circut(m_list)
    nu.rules_check(m_list)
    
    #生成带pipo的图
    g1 = CircuitGraph(m_list, include_pipo = True)
    g1.to_gexf_file('tmp\\%s_icpipo.gexf' % g1.name)
    g1.to_dot_file("tmp\\%s_icpipo.dot" % g1.name)
    
    #生成不带pipo的图
    g2 = CircuitGraph(m_list, include_pipo = False)
    g2.to_gexf_file('tmp\\%s_nopipo.gexf' % g2.name)
    g2.to_dot_file("tmp\\%s_nopipo.dot" % g2.name)
    if len(m_list) <= 20:
        for eachPrim in m_list:
            eachPrim.__print__()
            verbose_info =True
    else:
        verbose_info = False
        print "Info: THE m_list is too long >20. should not inspected by hand. ignore..."
    print "----NO PIPO-----------"
    g2.info(verbose_info)
    print "----Including PIPO----"    
    g1.info(verbose_info)
    return None

def fanout_stat(graph):

    '''统计图中的FD节点和组合逻辑节点的扇出，打印到标准输出上
    '''
    g1 = graph #local variable
    com_degree_stat = {} #组合逻辑扇出的统计
    fd_degree_stat = {}  #D触发器扇出数量的统计
    for eachNode in g1.nodes_iter():
        degree = g1.out_degree(eachNode)
        if isinstance(eachNode, cc.circut_module):
            if eachNode.m_type != 'FD':
                if not com_degree_stat.has_key( degree ):
                    com_degree_stat[degree] = 0
                com_degree_stat[ degree] += 1
            else:
                if not fd_degree_stat.has_key( degree ):
                    fd_degree_stat[degree]  =0
                fd_degree_stat[degree] += 1
    print "combinational node degree are:"
    for key, val in com_degree_stat.iteritems():
        print "%d %d" % (key, val)
    print "fd node degree stat are:"
    for key ,val in fd_degree_stat.iteritems():
        print "%d %d" % (key, val)
    return None
#------------------------------------------------------------------------------
if __name__ =='__main__':
    print "命令行帮助，可选命令如下"
    print "graph:输入一个文件名称，分别生成两个图（包含和不包含PIPO），保存图的信息到\\tmp下"
    print "fanout:输入一个文件名称，统计其中组合逻辑和FD节点的扇出数目统计"
    print "exit:退出主程序"
    while(1):
        cmd = raw_input("plz enter command:")
        if cmd == "graph" :
            __test()
        if cmd == "fanout":
            g1 = get_graph_from_raw_input()
            fanout_stat(g1)
        if cmd == "exit":
            break
