# -*- coding: utf-8 -*-

import sys
import os
import os.path
import re
import netlist_util   as nu
import netlist_parser.netlist_parser as np
import circut_class   as cc
#import generate_testbench as gt
#############################################################################################
def insert_scan_chain_new(fname,verbose=False,presult=True,\
                input_file_dir=os.getcwd(),output_file_dir=os.getcwd(),\
                K=6):
    input_file=os.path.join(input_file_dir,fname)    
    
    #file -->> m_list
    info=np.vm_parse(input_file)
    m_list=info['m_list']
    port_decl_list  =info['port_decl_list']
    signal_decl_list=info['signal_decl_list']
    assign_stm_list=[]
    if 'assign_stm_list' in info.keys():
        assign_stm_list=info['assign_stm_list']
    nu.mark_the_circut(m_list)
    
    #m_list -->>all info need 
    lut_type_cnt=[0,0,0,0,0,0]
    all_fd_dict =nu.get_all_fd(m_list,verbose)
    all_lut_dict=nu.get_all_lut(m_list,lut_type_cnt,verbose) 
    
    ##下面两个列表记录了需要进行修改的LUT和D触发器的
    lut_out2_FD_dict,FD_din_lut_list        =nu.get_lut_cnt2_FD(m_list,all_fd_dict,verbose,K)    
    
    ##和ce有关
    ce_signal_list,fd_has_ce_list           =nu.get_ce_in_fd(all_fd_dict,verbose)
    lut_cnt2_ce,un_opt_ce_list              =nu.get_lut_cnt2_ce(m_list,ce_signal_list,K,verbose)
    fd_ce_cnt=len(fd_has_ce_list)
    
    #gt.generate_testbench(m_list[0],fd_cnt=len(all_fd_dict),output_dir=output_file_dir)    
    #####################################################################    
    counter=0
    scan_out_list=[]
    
    #cnt for debug only
    fd_replace_cnt=0
    cnt_edited_lut=0
    #cnt for debug only 
    
    name_base=os.path.splitext(fname)[0]
    output_file=os.path.join(output_file_dir,name_base+'_insert_scan_chain.v')
    try:
        fobj=open(output_file,'w')
    except IOError,e:
        print "Error: file open error:",e
        return False
    fobj.writelines('`include "E:/ISE_WORKSPACE/scan_lib/scan_cells.v"\n')
    #--------------------------------------------------------------------------
    #全局信号增加
    #--------------------------------------------------------------------------
    _scan_in=cc.signal('input','scan_in',None)
    _scan_en=cc.signal('input','scan_en',None)
    _scan_out=cc.signal('output','scan_out',None)
    port_scan_in=_scan_in.signal_2_port()
    port_scan_en=_scan_en.signal_2_port()
    port_scan_out=_scan_out.signal_2_port()
    m_list[0].port_list.insert(0,port_scan_in)
    m_list[0].port_list.insert(0,port_scan_out)
    m_list[0].port_list.insert(0,port_scan_en)
    m_list[0].print_module()
    #--------------------------------------------------------------------------
    #primitive的修改
    #--------------------------------------------------------------------------
    for eachPrimitive in m_list[1:]:
        ##修改LUT增加MUX,进行扫描功能插入
        if eachPrimitive.m_type=='LUT' and (eachPrimitive.name in lut_out2_FD_dict.keys()):
            counter+=1
            input_num=lut_out2_FD_dict[eachPrimitive.name][0]
            scan_in=cc.port("I"+str(input_num),'input',cc.signal(name="scan_in"+str(counter)))            
            scan_en=cc.port('I'+str(input_num+1),'input',cc.signal(name="scan_en"))            
            eachPrimitive.port_list.insert(-1,scan_in)
            eachPrimitive.port_list.insert(-1,scan_en)
            assert (not eachPrimitive.param_list==None)
            assert len(eachPrimitive.param_list)==1
            old_init=eachPrimitive.param_list[0].value
            init_legal=re.match('(\d+)\'[hb]([0-9A-F]+)',old_init)
            assert (init_legal is not None)
            assert int(init_legal.groups()[0])==2**input_num
            if input_num==1:
                assert  (init_legal.groups()[0]=='2' and init_legal.groups()[1]=="1"),\
                "Error:find LUT1 .INIT !=2'h1 %s, is %s" % (eachPrimitive.name,eachPrimitive.param_list[0].value)
                NEW_INIT="8'hC5"
            else:
                NEW_INIT=str(2**(input_num+2))+'\'h'+'F'*int(2**(input_num-2)) \
                +'0'*int(2**(input_num-2))+(init_legal.groups()[1])*2
            eachPrimitive.param_list[0].edit_param('INIT',NEW_INIT)
            eachPrimitive.cellref=re.sub('LUT[1-4]',('LUT'+str(input_num+2)),eachPrimitive.cellref)
            scan_out_list.append(all_fd_dict[lut_out2_FD_dict[eachPrimitive.name][1]]['Q'].string)
            cnt_edited_lut+=1
        elif (eachPrimitive.m_type=='FD') and (eachPrimitive.name not in FD_din_lut_list):
            counter+=1
            eachPrimitive.cellref="SCAN_"+eachPrimitive.cellref
            SCAN_IN=cc.port('SCAN_IN','input',cc.signal(name="scan_in"+str(counter)))
            SCAN_EN=cc.port('SCAN_EN','input',cc.signal(name="scan_en"))
            SCAN_OUT=cc.port('SCAN_OUT','output',cc.signal(name='scan_out'+str(counter)))
            eachPrimitive.port_list.insert(0,SCAN_OUT)
            eachPrimitive.port_list.insert(0,SCAN_EN)
            eachPrimitive.port_list.insert(0,SCAN_IN)
            scan_out_list.append('scan_out'+str(counter))
            fd_replace_cnt+=1
        ##featured 7.4
        #--------------------------------------------------------------------------
        #CE时钟使能控制信号的优化     改LUT,进行时钟使能的插入,就是插入一个或门
        #--------------------------------------------------------------------------   
        elif(eachPrimitive.m_type=='LUT') and (eachPrimitive.name in lut_cnt2_ce):
            input_num=int(eachPrimitive.cellref[3])
            scan_en=cc.port('I'+str(input_num),'input',cc.signal(name="scan_en"))
            eachPrimitive.port_list.insert(-1,scan_en)
            assert (not eachPrimitive.param_list==None)
            assert len(eachPrimitive.param_list)==1
            old_init=eachPrimitive.param_list[0].value
            init_legal=re.match('(\d+)\'[hb]([0-9A-F]+)',old_init)
            assert (init_legal is not None)
            assert int(init_legal.groups()[0])==2**input_num
            if input_num==1:
                NEW_INIT="4'hD"
            else:
                NEW_INIT=str(2**(input_num+1))+'\'h'+'F'*int(2**(input_num-2))\
                        +old_init
            eachPrimitive.param_list[0].edit_param('INIT',NEW_INIT)
            eachPrimitive.cellref=re.sub('LUT[1-4]',('LUT'+str(input_num+1)),eachPrimitive.cellref)    
        elif (eachPrimitive.m_type=='FD') and (eachPrimitive.name in fd_has_ce_list):
            current_ce=all_fd_dict[eachPrimitive.name]['CE'].string 
            if current_ce in un_opt_ce_list:
                new_ce_signal=cc.signal('wire','gated_'+current_ce)
                eachPrimitive.edit_spec_port('CE',new_ce_signal)
                signal_decl_list.append(new_ce_signal)
            
    #--------------------------------------------------------------------------
    #扫描链顺序的确定,在结尾处进行assign
    #--------------------------------------------------------------------------
    assign_stm_list.append(cc.assign('assign',"scan_in1","scan_in"))
    for i in range(2,counter+1):
        tmp_assign=cc.assign('assign',"scan_in"+str(i),scan_out_list[i-2])
        assign_stm_list.append(tmp_assign)
    assign_stm_list.append(cc.assign('assign',"scan_out",scan_out_list[counter-1]))
    
    #--------------------------------------------------------------------------
    #检查是否成功
    #check all the numbers ,insure all wanted LUT and FD been handled
    #--------------------------------------------------------------------------
    assert (fd_replace_cnt+cnt_edited_lut)==len(all_fd_dict),"not all the FD has been scaned !!"
    assert (cnt_edited_lut==len(FD_din_lut_list)),"There is Usefully LUT not edited !!"
    #--------------------------------------------------------------------------
    #进行文件的打印或者直接输出到stdout上面
    #--------------------------------------------------------------------------
    if fobj:
        console=sys.stdout
        sys.stdout=fobj
        m_list[0].print_module()
        for eachPipo in port_decl_list:
            eachPipo.__print__(pipo_decl=True)
        for eachWire in signal_decl_list:
            eachWire.__print__(is_wire_decl=True)
        for eachModule in m_list[1:]:
            assert isinstance(eachModule,cc.circut_module), eachModule
            eachModule.print_module()
        if assign_stm_list:
            for eachAssign in assign_stm_list:
                eachAssign.__print__()
        for eachCE in un_opt_ce_list:
            print "assign gated_%s = scan_en?1'b1: %s ;"%(eachCE,eachCE)
        print "//this is a file generate by @litao"
        print "endmodule"
        sys.stdout=console
    fobj.close()
    if presult:
        print 'Info:LUT cnt is      : '+str(len(all_lut_dict.keys()))
        print 'Info:LUT1-6 number is: '+str(lut_type_cnt)
        print 'Info:FD CNT is       : '+str(counter)+":::"+str(len(all_fd_dict))
        print 'Info:replace FD CNT  : '+str(fd_replace_cnt)
        print 'Info:Useful LUT CNT  : '+str(len(FD_din_lut_list))
        print 'Info:edited LUT CNT  : '+str(cnt_edited_lut)
        print 'Info:FD has a CE CNT : '+str(fd_ce_cnt)
        print 'Info:ce_signal CNT is: '+str(len(ce_signal_list))
    print 'Job: Replace '+fname+' done\n\n'
    return True
#############################################################################################
if __name__=='__main__':
    if len(sys.argv)==1:
        print "Just handle one simple verilog netlist in os.get_cwd() dir"
        fname=raw_input("plz enter the file name:")
        k=int(raw_input("plz enter K:"))
        insert_scan_chain_new(fname,K=k)
    elif sys.argv[1]=='-many':    
        parent_dir=os.getcwd()
        while(1):
            tmp1=raw_input('Plz enter the verilog source sub dir:')
            input_file_dir=parent_dir+"\\test_input_netlist\\"+tmp1
            if os.path.exists(input_file_dir)==False:
                print 'Error : this dir dont exists!'
                continue
            else:
                break
        flag=True
        while(flag):
            tmp2=raw_input('Plz enter the output sub dir:')
            output_file_dir=parent_dir+"\\test_output_dir\\"+tmp2
            if os.path.exists(output_file_dir)==False:
                print 'the dir: '+output_file_dir+' dont exists'
                flag=os.mkdir(output_file_dir)
                print 'create a dir : '+output_file_dir
            else:
                break           
        K=int(raw_input('plz enter the K parameter of FPGA:K='))
        assert (K==6 or K==4),"K not 4 or 6"
        print "Note: current path: "+parent_dir
        print "Note: output_file_path: "+output_file_dir
        print "Note: input_file_path: "+input_file_dir
    #    __console__=sys.stdout
    #    log_obj=open("exec_log.txt",'w')
    #    sys.stdout=log_obj
        for eachFile in os.listdir(input_file_dir):
            print  eachFile
            if os.path.splitext(eachFile)[1] in ['.v','.vm']:
                insert_scan_chain_new(eachFile,False,True,input_file_dir,output_file_dir,K)
            else:
                continue
    #    sys.stdout=__console__
    #    log_obj.close()
        print "Job :Thingd down!!!"

