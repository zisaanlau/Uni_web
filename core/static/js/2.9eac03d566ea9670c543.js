webpackJsonp([2],{"0wMN":function(e,t,i){"use strict";var a=i("8YIr"),n=i.n(a);t.a={data:function(){return{fetchMethodKey:"search",inquire:{pageNum:1,pageSize:10},pageSizes:n()([10,20,30,50]),pageLayout:"total, prev, pager, next, sizes, jumper"}},methods:{indexMethod:function(e){return(this.inquire.pageNum-1)*this.inquire.pageSize+(e+1)},pageSizeChange:function(e){this.inquire.pageSize=e,this.inquire.pageNum=1,this[this.fetchMethodKey]()},pageCurrentChange:function(e){this.inquire.pageNum=e,this[this.fetchMethodKey]()}}}},"5W3t":function(e,t){},"8YIr":function(e,t,i){e.exports={default:i("MKNx"),__esModule:!0}},Bp0I:function(e,t,i){var a=i("EqjI"),n=i("06OY").onFreeze;i("uqUo")("seal",function(e){return function(t){return e&&a(t)?e(n(t)):t}})},MKNx:function(e,t,i){i("Bp0I"),e.exports=i("FeBl").Object.seal},"k/0R":function(e,t,i){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var a=i("Xxa5"),n=i.n(a),r=i("exGp"),l=i.n(r),s=i("gyMJ");function o(e){return Object(s.a)({url:"/sysApi/get_works",method:"post",data:e})}var c={name:"UserWorks",mixins:[i("0wMN").a],data:function(){return{imgUrl:Object({NODE_ENV:"production",VUE_APP_API_BASE_URL:"",VUE_APP_API_VOICE_URL:"https://v1.reecho.cn/api/",VUE_APP_API_CHAT_URL:"https://api.lingyiwanwu.com/"}).VUE_APP_BASE_API+"/index/ucenter/upload_img",site_code:"",username:"",multipleSelection:[],time_type:"1",is_enable:1,start_time:"",end_time:"",tabletotal:0,options:[{value:1,label:"是"},{value:0,label:"否"}],tableData:[],dialogFormAdd:!1,dialogVisibleIfarme:!1,form:{site_code:"",site_name:"",item:[],start_time:"",end_time:"",is_enable:"1",remark:""},formType:"",rules:{site_name:[{required:!0,message:"请输入网点名称",trigger:"blur"}],site_code:[{required:!0,message:"请输入网点编码",trigger:"blur"}],is_enable:[{required:!0,message:"请选择启用状态",trigger:"change"}],item:[{required:!0,message:"服务项目必选",trigger:"change"}],start_time:[{required:!0,message:"请选择开始履行合同时间",trigger:"change"}],end_time:[{required:!0,message:"请选择结束履行合同时间",trigger:"change"}],remark:[{required:!1,message:"",trigger:"blur"}]},rolelist:[],formLabelWidth:"140px",exportUrl:"",dialogTitle:"",fileList:[],centerDialogVisible:!1,imgShowUrl:[],secoptions:[],secLoading:!1,loadinghandleSearch:!1,loadingsubmit:!1}},created:function(){this.search()},methods:{handleSearch:function(){this.inquire.pageNum=1,this.search()},search:function(){var e=this;return l()(n.a.mark(function t(){var i,a;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return e.loadinghandleSearch=!0,(i=new FormData).append("username",e.username),i.append("pageSize",e.inquire.pageSize),i.append("page",e.inquire.pageNum),t.next=7,o(i);case 7:a=t.sent,e.loadinghandleSearch=!1,e.tableData=a.data.rows||[],e.tabletotal=a.data.total;case 11:case"end":return t.stop()}},t,e)}))()},reset:function(){this.site_code="",this.time_type="1",this.start_time="",this.end_time="",this.is_enable=1},close:function(){this.loadingsubmit=!1,this.dialogFormAdd=!1,this.$refs.form.resetFields()},operatTable:function(e){var t=this;if(this.dialogTitle="add"===e?"新增网点":"修改网点信息",this.formType=e,this.form={site_code:"",site_name:"",item:[],start_time:"",end_time:"",is_enable:1,remark:""},this.fileList=[],this.dialogFormAdd=!0,"edit"===e){if(1!==this.multipleSelection.length)return void this.$message.error("请选择一条数据进行修改!");var i=this.multipleSelection[0];this.form={site_code:i.site_code,site_name:i.site_name,item:i.item_arr,start_time:i.start_time,end_time:i.end_time,is_enable:i.is_enable,remark:i.remark};for(var a=[],n=0;n<i.img_url_arr.length;n++){var r={};r.name=i.img_url_arr[n].short_url,r.url=i.img_url_arr[n].long_url,a.push(r)}this.fileList=a}else this.$nextTick(function(){t.$refs.form.clearValidate()})},deleteData:function(){var e=this;0!==this.multipleSelection.length?this.$confirm("此操作将永久删除选中的"+this.multipleSelection.length+"条数据, 是否继续?","提示",{confirmButtonText:"确定",cancelButtonText:"取消",type:"warning"}).then(function(){var t,i=e.multipleSelection.map(function(e){return e.id});(t={id:i},Object(s.a)({url:"/sysApi/deleteWork",method:"post",data:t})).then(function(t){t.success?(e.$message({type:"success",message:"删除成功!"}),e.search()):e.$message.error(t.msg)})}).catch(function(){e.$message({type:"info",message:"已取消删除"})}):this.$message.error("请选择要删除的数据!")},handleSelectionChange:function(e){this.multipleSelection=e}}},u=i("XyMi");var m=function(e){i("5W3t")},d=Object(u.a)(c,function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("div",{staticClass:"app-main"},[i("div",{staticClass:"margin-t"},[i("el-button",{attrs:{type:"primary",loading:e.loadinghandleSearch},on:{click:e.handleSearch}},[e._v(" 查询 ")]),e._v(" "),i("el-button",{on:{click:e.reset}},[e._v(" 重置 ")]),e._v(" "),i("el-button",{attrs:{type:"primary",disabled:1!==e.multipleSelection.length},on:{click:function(t){e.operatTable("edit")}}},[e._v(" 修改 ")]),e._v(" "),i("el-button",{attrs:{type:"danger",disabled:0===e.multipleSelection.length},on:{click:e.deleteData}},[e._v(" 删除 ")])],1),e._v(" "),i("div",{staticClass:"search-body margin-t-sm"},[i("div",{staticClass:"fl margin-t-sm margin-r-sm"},[i("span",[e._v("用户名：")]),e._v(" "),i("el-input",{staticClass:"input-w",attrs:{clearable:"",placeholder:"请输入"},model:{value:e.username,callback:function(t){e.username=t},expression:"username"}})],1)]),e._v(" "),i("div",{staticClass:"margin-t-lg"},[i("el-table",{ref:"Table",staticStyle:{width:"100%"},attrs:{data:e.tableData,stripe:"",border:"",height:"550"},on:{"selection-change":e.handleSelectionChange}},[i("el-table-column",{attrs:{type:"selection",width:"55"}}),e._v(" "),i("el-table-column",{attrs:{prop:"id",label:"id",align:"center","min-width":"40"}}),e._v(" "),i("el-table-column",{attrs:{prop:"username",label:"用户id",align:"center","min-width":"80"}}),e._v(" "),i("el-table-column",{attrs:{prop:"input_text",align:"center",label:"文案","min-width":"200"}}),e._v(" "),i("el-table-column",{attrs:{prop:"output_img_path",align:"center",label:"预览封面路径","min-width":"200"}}),e._v(" "),i("el-table-column",{attrs:{prop:"input_file_path",align:"center",label:"用户文件","min-width":"200"}}),e._v(" "),i("el-table-column",{attrs:{prop:"credit_cost",align:"center",label:"花费积分","min-width":"80"}}),e._v(" "),i("el-table-column",{attrs:{prop:"input_audio_path",align:"center",label:"用户语音文件","min-width":"200"}}),e._v(" "),i("el-table-column",{attrs:{prop:"output_video_path",align:"center",label:"数字人路径","min-width":"200"}}),e._v(" "),i("el-table-column",{attrs:{prop:"username",align:"center",label:"创建人",width:"120"}}),e._v(" "),i("el-table-column",{attrs:{prop:"create_time",align:"center",label:"创建时间",width:"160"}})],1),e._v(" "),i("div",{staticClass:"text-right margin-t-sm"},[i("el-pagination",{attrs:{background:"","page-sizes":e.pageSizes,"current-page":e.inquire.pageNum,"page-size":e.inquire.pageSize,layout:e.pageLayout,total:e.tabletotal},on:{"size-change":e.pageSizeChange,"current-change":e.pageCurrentChange}})],1)],1)])},[],!1,m,"data-v-0e959cee",null);t.default=d.exports},uqUo:function(e,t,i){var a=i("kM2E"),n=i("FeBl"),r=i("S82l");e.exports=function(e,t){var i=(n.Object||{})[e]||Object[e],l={};l[e]=t(i),a(a.S+a.F*r(function(){i(1)}),"Object",l)}}});
//# sourceMappingURL=2.9eac03d566ea9670c543.js.map