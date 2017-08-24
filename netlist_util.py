# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 16:30:03 2015
@author: litao
this file is composed of a lot of functions to parse and util the netlist Src file
"""

import re
import copy

from netlistx.circuit import port

def mark_the_circut(primtives, allow_dsp=False, allow_unkown=True ):
    'mark all the module with a type'
    cellref_list=[]
    FD_TYPE=('FDCE','FDPE','FDRE','FDSE', "FDRS","FDRSE",'FDC','FDP','FDR','FDS','FDE', 'FD')
    LUT_TYPE=('LUT1','LUT2','LUT3','LUT4','LUT5','LUT6',
              'LUT1_L','LUT2_L','LUT3_L','LUT4_L','LUT5_L','LUT6_L',
              'LUT6_2')
    OTHER_COMBIN=('MUXCY','MUXCY_L','MUXF7','MUXF8','XORCY','INV','MULT_AND','MUXF5',
                  'MUXF6')
    for prim in primtives:
        if prim.cellref not in cellref_list:
            cellref_list.append(prim.cellref)
        #FD--------------------------------------------------------------------
        if re.match('FD\w*',prim.cellref) is not None:
            assert prim.cellref in FD_TYPE,\
                "%s ,%s not in predefined FD_TYPE"%(prim.cellref,prim.name)
            prim.m_type='FD'
            for eachPort in prim.port_list:
                if eachPort.port_name in ('D', 'CE','R','S','CLR','PRE'):
                    eachPort.port_type = port.PORT_TYPE_INPUT
                elif eachPort.port_name == 'Q':
                    eachPort.port_type = port.PORT_TYPE_OUTPUT
                elif eachPort.port_name == 'C':
                    eachPort.port_type = port.PORT_TYPE_CLOCK
                else:
                    raise AssertionError, "FD has no defined thie port: %s"% eachPort.port_name
        # LUT------------------------------------------------------------------
        elif re.match('LUT\w+',prim.cellref) is not None:
            prim.m_type='LUT'
            assert prim.cellref in LUT_TYPE,\
                "%s ,%s not in predefined LUT_TYPE"%(prim.cellref,prim.name)
            for eachPort in prim.port_list:
                if eachPort.port_name[0] == 'I':
                    eachPort.port_type =  port.PORT_TYPE_INPUT
                else:
                    assert eachPort.port_name in ['O','LO','O5','O6'],\
                        prim.cellref+"  "+prim.name+"  "+eachPort.port_name
                    eachPort.port_type = port.PORT_TYPE_OUTPUT

        # MUX and XOR----------------------------------------------------------
        elif prim.cellref in OTHER_COMBIN:
            prim.m_type=prim.cellref
            for eachPort in prim.port_list[:-1]:
                eachPort.port_type = port.PORT_TYPE_INPUT
            prim.port_list[-1].port_type = port.PORT_TYPE_OUTPUT
            
        #BUF------------------------------------------------------------------
        elif re.match('\w*BUF\w*',prim.cellref) is not None:
            prim.m_type='BUF'
            for eachPort in prim.port_list:
                assert eachPort.port_name in ['I','O'],\
                    "BUF:%s has a port neither I or O" %prim.name
                if eachPort.port_name=='I':
                    eachPort.port_type = port.PORT_TYPE_INPUT
                elif eachPort.port_name=='O':
                    eachPort.port_type = port.PORT_TYPE_OUTPUT
        #GND VCC---------------------------------------------------------------
        elif (prim.cellref=='GND' or prim.cellref=='VCC'):
            prim.m_type=prim.cellref
            assert len(prim.port_list)==1, "GND VCC:%s has more than 1 port."  % prim.name 
            for eachPort in prim.port_list:
                eachPort.port_type = port.PORT_TYPE_OUTPUT

        #DSP48E---------------------------------------------------------------
        elif re.match('DSP48|DSP48E\w*',prim.cellref) is not None:
            prim.m_type='DSP'
            if not allow_dsp:
                raise AssertionError,"Error:find %s : %s in this netlist"\
                    %(prim.cellref,prim.name)
            else:
                print "Warning:find %s : %s in this netlist"\
                        %(prim.cellref,prim.name)
        else:
            if not allow_unkown:
                raise AssertionError,\
                 'Error:unknown cellref:'+prim.cellref+"  "+prim.name+'\n'+\
                      "plz update the mark_the_circut() to keep this programe pratical"
            else:
                print 'Warning:unknown cellref:'+prim.cellref+"  "+prim.name+'\n'+\
                      "plz update the mark_the_circut() to keep this programe pratical"
    return cellref_list

def get_all_fd(m_list,verbose=False):
    '''--get all the FD and its port list--
        retutn :all_fd_dict = { eachFD.name: port_info{...} } 
                #port_info ={port1.name:port_assign, port2.name:port_assign,....}
    '''
    all_fd_dict={}
    if verbose:
        print 'Info: all the FD and its port_assign.string are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='FD':
            port_info={}
            for eachPort in eachModule.port_list:
                port_info[eachPort.port_name]=eachPort.port_assign
            assert not all_fd_dict.has_key(eachModule.name),\
                "%s:%s"%(eachModule.cellref,eachModule.name)
            all_fd_dict[eachModule.name]=port_info
            if verbose:
                print "%s %s :"%(eachModule.cellref,eachModule.name),
                for eachPort in port_info.keys():
                    print ".%s(" % eachPort,
                    port_info[eachPort].__print__()
                    print ") ",
                print '\n'
    print "Note: get_all_fd() sucessfully !"
    return all_fd_dict

def get_all_lut(m_list,lut_type_cnt=[0]*6,verbose=False):
    ''''get_all_lut(m_list,lut_type_cnt,verbose)
        ->>the all_lut_dict,key is name, calue is cellref and port_info'''
    all_lut_dict={} 
    if verbose:
        print 'Info: all the LUT and its name Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='LUT':
            if verbose:
                print "%s:%s"%(eachModule.cellref,eachModule.name)
            port_info={}
            for eachPort in eachModule.port_list:
                port_info[eachPort.port_name]=eachPort.port_assign
            assert not all_lut_dict.has_key(eachModule.name),"%s:%s"%\
                (eachModule.cellref, eachModule.name)
            all_lut_dict[eachModule.name]=[eachModule.cellref,port_info]
            lut_kind=int(eachModule.cellref[3])-1
            lut_type_cnt[lut_kind]=lut_type_cnt[lut_kind]+1 
    assert len(all_lut_dict.keys())==sum(lut_type_cnt),'Assertion Error: LUT cnt error'
    return all_lut_dict
    
def get_lut_cnt2_FD(m_list,all_fd_dict,verbose=False,K=6):
    '''get all the LUT that has a connection to a FDs D port ,and PIN_NUM <= K-2
        return: 
              FD_din_lut_list, prim对象列表，每一个有可用LUT的FD对象
              lut_out2_fd_dict, 字典，key=LUT名称字符串类型，value= (int_PIN_NUM, FD_Prim Instance)  
    '''
    FD_din_lut_list=[]
    lut_out2_FD_dict={}
    if verbose:
        cnt=0
        print 'Info: all the Lut has output connect to FD\'s .D port Are:'
    for each_FD in all_fd_dict.keys():  
        cuurent_d_assign=all_fd_dict[each_FD]['D'].string
        for eachModule in m_list[1:]:       
            if eachModule.m_type=='LUT' and  int(eachModule.cellref[3])<=(K-2) \
                    and eachModule.been_searched==False :
                ##一般来讲，取最后一个LUT的端口作为输出是对的，但是对于LUT6_2的情况，有O5,O6两个端口
                ##但是对于LUT6_2来讲，这些都不重要，因为永远不会连接到LUT6_2.只记录了有小于K-2个端口的LUT
                assert eachModule.port_list[-1].port_name in ['O','LO']
                current_lut_out=eachModule.port_list[-1].port_assign.string
                if current_lut_out==cuurent_d_assign:
                    eachModule.been_searched=True
                    FD_din_lut_list.append(each_FD) 
                    lut_out2_FD_dict[eachModule.name]=[int(eachModule.cellref[3]),each_FD]
                    if verbose:
                        print '%s.D <--- %s %s'%(each_FD,eachModule.cellref,eachModule.name)
                        cnt=cnt+1                    
                    #一个FD的端口最多只能连接到一个LUT的输出上面，所以找到之后跳出循环，进行下一个FD
                    break
    if verbose:
        print "Info: found %d (K-2)LUT connected to FD's D port."% cnt
    print 'Note: get_lut_cnt2_FD() successfully !'
    return lut_out2_FD_dict,FD_din_lut_list

def get_clk_in_fd(all_fd_dict,verbose=False):
    clock_list=[]
    for eachFD in all_fd_dict.keys():
        assert all_fd_dict[eachFD].has_key("C"),"Error:FD %s has no C port" % eachFD
        current_clk=all_fd_dict[eachFD]['C'].string
        if current_clk not in clock_list:
            clock_list.append(current_clk)
    assert len(clock_list)<=1,\
        "AssertError: has %d clock domain\n %s " % (len(clock_list),\
            ",".join(clock_list) )
    if verbose:
        print "Info:all clock signals are as follows:\n    ",
        for clock in  clock_list:
            print clock
    print "Note: get_all_clock() successfully !"
    return clock_list
    
def get_ce_in_fd(all_fd_dict,verbose=False):
    '''para: 
            all_fd_dict,verbose=False
       return:
            ce_signal_list，字符串列表，每一个元素为ce信号的string属性，也就是名称
            fd_has_ce_list，字符串列表，每一个元素为有CE信号的FD的名称
    '''
    ce_signal_list=[]
    fd_has_ce_list=[]
    for eachFD in all_fd_dict.keys():
         if all_fd_dict[eachFD].has_key('CE'):
             fd_has_ce_list.append(eachFD)
             current_ce=all_fd_dict[eachFD]['CE'].string
             if current_ce not in ce_signal_list:
                 ce_signal_list.append(current_ce)
    if verbose:
        if ce_signal_list:
            print "Info: all ce signal are as follows:\n    ",
            for ce in ce_signal_list:    
                print ce
        else:
            print "Info: no ce found in netlist"
    print"Note: get_ce_in_fd() successfully !"
    return ce_signal_list,fd_has_ce_list

def get_reset_in_fd(all_fd_dict,verbose=False):
    'get all the async and sync reset of all fd in this m_list'
    async_reset_list=[]    
    reset_list=[]    
    for eachFD in all_fd_dict.keys():
        if all_fd_dict[eachFD].has_key('CLR'):
            current_asyn_reset_assign=all_fd_dict[eachFD]['CLR'] #its a cc.signal obj
            current_asyn_reset=current_asyn_reset_assign.string  #get its string attr as unique
            if current_asyn_reset not in async_reset_list:
                async_reset_list.append(current_asyn_reset)
        elif all_fd_dict[eachFD].has_key('PRE'):
            current_asyn_reset_assign=all_fd_dict[eachFD]['PRE'] #its a cc.signal obj
            current_asyn_reset=current_asyn_reset_assign.string  #get its string attr as unique
            if current_asyn_reset not in async_reset_list:
                async_reset_list.append(current_asyn_reset)
        elif all_fd_dict[eachFD].has_key('R'):
            current_reset_assign=all_fd_dict[eachFD]['R']
            current_reset=current_reset_assign.string
            if current_reset not in reset_list:
                reset_list.append(current_reset)
        elif all_fd_dict[eachFD].has_key('S'):
            current_reset_assign=all_fd_dict[eachFD]['S']
            current_reset=current_reset_assign.string
            if current_reset not in reset_list:
                reset_list.append(current_reset)
    if verbose:
        print "Info: all the Async Reset Signal Are:\n    ",
        print ",".join(async_reset_list)
        print "Info: all the Sync Reset Signal Are:\n    ",
        print ",".join(reset_list)
    print "Note: get_reset_in_fd() successfully"
    return reset_list,async_reset_list
    

def get_lut_cnt2_ce(m_list,ce_signal_list,K=6,verbose=False):
    '''para: 
            m_list, ce_signal_list, K=6, verbose =False
       return: 
            lut_cnt2_ce    字符串列表：每一个元素为，PIN_NUM<= K-2，且没有被搜索过的，
                             输出口与CE相连接的LUT的name
            un_opt_ce_list 字符串列表：每一个元素为，没有被优化的CE信号名称，这样的信号
                           需要在末尾处进行assign赋值，将其用scan_en gated掉
               
    '''
    lut_cnt2_ce=[]
    opt_ce_flag=False
    un_opt_ce_list=copy.deepcopy(ce_signal_list)
    # TODO:优化这个函数的速度，将循环的层次改变一下
    for eachCE in ce_signal_list:
        for eachModule in m_list[1:]:
            if eachModule.m_type=="LUT" and  eachModule.been_searched==False :
                if eachModule.port_list[-1].port_assign.string==eachCE \
                    and int(eachModule.cellref[3])<=(K-1):
                    eachModule.been_searched=True
                    opt_ce_flag=True
                    lut_cnt2_ce.append(eachModule.name)
        if opt_ce_flag==True:
            un_opt_ce_list.remove(eachCE)
            opt_ce_flag=False                 
    if verbose:
        print "Info : lut has a output connnet to CE are:"
        for x in lut_cnt2_ce:
            print x
    print "Note: get_lut_cnt2_ce() !"
    return lut_cnt2_ce,un_opt_ce_list
      
def rules_check(m_list):
    '''保证只有一个时钟域，保证时钟和复位信号都是通过外部引脚进行控制的。
    ''' 
    print "Process: check rules of netlist to construct graph..."
    special_signal = {}
    print "Process: finding all fd in netlist..."
    all_fd_dict = get_all_fd(m_list)
    print "Process: finding all clks connect to fd..."
    clock_signal = get_clk_in_fd(all_fd_dict, True)
    print "Process: finding all reset and async reset of fd..."
    reset_list, async_reset_list = get_reset_in_fd(all_fd_dict, True)

    single_bit_pi = []
    if len(clock_signal) == 1 : # 时钟个数为0时 ， 不用检查时钟了
        clock_flag = False    
        for eachPi in m_list[0].port_list:
            if eachPi.port_type == port.PORT_TYPE_INPUT and eachPi.port_width == 1:
                if clock_signal[0] == eachPi.name:
                    clock_flag = True
                single_bit_pi.append(eachPi.name)
        if not clock_flag:
            raise AssertionError,"CLOCK signal is not cnnected to any PI"
    for anyReset in reset_list:
        if not anyReset in single_bit_pi:
            raise AssertionError,"Reset signal %s not connected to any PI"% anyReset
    for anyAsyncReset in async_reset_list:
        if not anyAsyncReset in single_bit_pi:
            raise AssertionError,"Async Reset signal %s not connected to any PI"% anyAsyncReset
    special_signal={ 'CLOCK':clock_signal,
                    'SYNC_RESET':reset_list,
                    'ASYNC_RESET':async_reset_list}
    print "Info: Rules check successfully, no rules vialation to model with a graph"
    return special_signal



