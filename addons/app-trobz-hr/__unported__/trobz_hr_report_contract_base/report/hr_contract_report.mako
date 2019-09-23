<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<head>
    <style type="text/css">
        body{
        	font-family: "Arial", sans-serif; 
        	font-size: 12px;
        }
         
        #main{font-family: "Arial", sans-serif; 
        	font-size: 10pt; 
        	so-language: en-US;
        	width: 650px;
        	padding: 0;
        	margin-left: auto;
        	margin-right: auto;
        }
        #head_left{
        	line-height: 20px;
        	width: 350px;
        	float: left;
        	height: 80px;
        }
        #head_right{
            text-align: center;
        	line-height: 20px;
        	width: 300px;
        	float: left;
        	height: 80px;
        }
        #title{
        	line-height: 30px;
        	text-align: center;
        	height: 80px;
        	clear: both;
        	font-size: 20px;
        	font-weight: bold;
        }
        #content{
            line-height: 20px;
        	height: 500px;
        	clear: both;
        }
        #content_col_350{
            padding-top: 10px;
            line-height: 20px;
            width: 350px;
            float: left;
        }
        #content_col_300{
            padding-top: 10px;
            line-height: 20px;
            width: 300px;
            float: left;
        }
        #content_col_300_no_padding{
            line-height: 20px;
            width: 300px;
            float: left;
        }
        #content_col_200{
            padding-top: 10px;
            line-height: 20px;
            width: 200px;
            float: left;
        }
        #content_full{
            padding-top: 4px;
            padding-bottom: 4px;
            line-height: 20px;
            clear: both;
        }
        #content_full_no_padding{
            line-height: 20px;
            clear: both;
        }
        #content_full_pad_left{
            padding-left: 30px;
            line-height: 20px;
            clear: both;
        }
        #content_heading{
            padding-top: 10px;
            line-height: 20px;
            clear: both;
            font-weight: bold;
            counter-increment: orhead;
        }
        #italic {
            padding-top: 2px;
            padding-bottom: 2px;
            font-style: italic;
        }
        #footer_left{
            line-height: 20px;
            width: 350px;
            float: left;
            text-align: center;
            height: 100px;
            margin-top: 30px;
        }
        #footer_right{
            line-height: 20px;
            width: 300px;
            float: left;
            text-align: center;
            height: 100px;
            margin-top: 30px;
        }
        .list {
            counter-reset: foo;
            padding: 0;
            margin: 0 0 0 0;
        }
        .list li {
            display: table;
            list-style-type: none;
        }
        .list li:before {
            display: table-cell;
            counter-increment: foo; 
            padding-right: 10px;
            content: counter(orhead) "." counter(foo) "  ";
        }
    </style>
</head>
<BODY LANG="en-US" DIR="LTR">
%for object, docs in get_contract():
<div id="main">
	<div id="head_left">
		${company.name}
        <br/>
		<div id="italic"> ${company.name}</div>
	</div>
	<div id="head_right">
		CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM
        <br/>
		<div id="italic">THE SOCIALIST REPUBLIC OF VIETNAM</div>
	</div>
	<div id="head_left">
       Số: ${object.name}
    </div>
    <div id="head_right">
        Độc lập - Tự do - Hạnh phúc
        <br/>
        <div id="italic">Independence – Freedom – Happiness</div>
    </div>
	<div id="title">
		HỢP ĐỒNG LAO ĐỘNG
        <br/>
		<div id="italic">LABOR CONTRACT</div>
	</div>
	<div id="content">
		<div id="content_full">
			Được ban hành theo Thông tư số 21/2003/TT-BLĐTBXH ngày 22 tháng 9 năm 2003 của Bộ Lao động - Thương Binh và Xã hội
		  <br/>
			<div id="italic">Issued under the Circular No.21/2003/TT-BLDTBXH dated 22 September 2003 of the Ministry of Labor, Invalid and Social Affairs</div>
		</div>
		<div id="content_col_300">
		  <b>Chúng tôi, một bên là: ${object.employee_id.parent_id.name}</b>
		  <br/>
		  <div id="italic">We are, from one side: ${object.employee_id.parent_id and object.employee_id.parent_id.name or ''}</div>
		</div>
		<div id="content_col_350">
			Chức vụ: ${object.employee_id.parent_id and object.employee_id.parent_id.job_id and object.employee_id.parent_id.job_id.name or 'Giám Đốc'}
			<br/>
			<div id="italic">Position: ${object.employee_id.parent_id and object.employee_id.parent_id.job_id and object.employee_id.parent_id.job_id.name or 'General Manager'}</div>
		</div>
		<div id="content_full">
			Đại diện cho: ${company.name}
			<br/>
			<div id="italic">On behalf of: ${company.name}</div>
		</div>
		<div id="content_full">
			Địa chỉ: ${company.street}, ${company.city}
			<br/>
			<div id="italic">Address: ${company.street}, ${company.city}</div>
		</div>
		<div id="content_full">
			Số điện thoại: ${company.phone}
			<br/>
			<div id="italic">Tel: ${company.phone}</div>
		</div>
		<div id="content_full">
			<b>Và một bên là: ${object.employee_id.name}</b> 
			<br/>
			<div id="italic">And from other side: ${object.employee_id.name}</div>
		</div>
	    <div id="content_full">
			Ngày sinh: ${object.employee_id.birthday and date_format(object.employee_id.birthday) or ''}
			<br/>
			<div id="italic">Date of birth: ${object.employee_id.birthday and date_format(object.employee_id.birthday) or ''}</div>
		</div>
		<div id="content_col_300">
		   Trình độ: 
		   <br/>
	       <div id="italic">Degree: </div>
		</div>
		<div id="content_col_350">
			Chuyên môn: 
			<br/>
			<div id="italic">Profession: </div>
		</div>
	    <div id="content_full">
			Địa chỉ: ${object.employee_id.address_home_id and object.employee_id.address_home_id.street + ', ' + object.employee_id.address_home_id.city or ''}
			<br/>
			<div id="italic">Home address: ${object.employee_id.address_home_id and object.employee_id.address_home_id.street + ', ' + object.employee_id.address_home_id.city or ''}</div>
		</div>
		<div id='content_col_200'>
			CMND số: ${docs.get('Identification Card', False) and docs['Identification Card'].name or ''}
			<br/>
			<div id="italic">ID card no: ${docs.get('Identification Card', False) and docs['Identification Card'].name or ''}</div>
		</div>
		<div id='content_col_200'>
			Cấp ngày: ${docs.get('Identification Card', False) and docs['Identification Card'].issue_date and date_format(docs['Identification Card'].issue_date) or ''}
			<br/>
		    <div id="italic">Issue date: ${docs.get('Identification Card', False) and docs['Identification Card'].issue_date and date_format(docs['Identification Card'].issue_date) or ''}</div>
		</div>
		<div id='content_col_200'>
			Tại: ${docs.get('Identification Card', False) and docs['Identification Card'].issue_place or ''}
			<br/>
		    <div id="italic">Issue at: ${docs.get('Identification Card', False) and docs['Identification Card'].issue_place or ''}</div>
		</div>
		<div id="content_col_300">
		    Sổ lao động số (nếu có): ${docs.get('Labor Book', '') and docs['Labor Book'].name or ''}
	        <br/>
	        <div id="italic">Labor book no (If any): ${docs.get('Labor Book', '') and docs['Labor Book'].name or ''}</div>
		</div>
		<div id="content_col_200">
		   Cấp ngày: ${docs.get('Labor Book', '') and docs['Labor Book'].issue_date and date_format(docs['Labor Book'].issue_date) or ''}
		   <br/>
	       <div id="italic">Issue date: ${docs.get('Labor Book', '') and docs['Labor Book'].issue_date and date_format(docs['Labor Book'].issue_date) or ''}</div>
		</div>
		<div id="content_full">
		    Điện thoại: ${object.employee_id.work_phone or ''}
	        <br/>
	        <div id="italic">Tel: ${object.employee_id.work_phone or ''}</div>
		</div>
	    <div id="content_full">
			Đồng ý ký hợp đồng lao động này (Hợp đồng) với những điều khoản và điều kiện như sau:
			<br/>
			<div id="italic">Agreed to sign this labor contract (the “Contract”) with the following terms and conditions:</div>
		</div>
	    <div id="content_heading">
			Điều 1: Điều khoản và công việc trong Hợp đồng
			<br/>
			<div id="italic">Article 1: Term and job in labor contract</div>
		</div>
	    <div id="content_full">
	        <ol class="list">
	            <li>
	            Loại Hợp đồng: ${object.type_id and object.type_id.name or ''}
	            <br/>
	            Từ ngày ${object.date_start[8:]} tháng ${object.date_start[5:7]} năm ${object.date_start[:4]} ${object.date_end and u' đến ngày ' + object.date_start[8:] + u' tháng '+ object.date_start[5:7] + u' năm ' + object.date_start[:4] or ''}
	            <br/>
	            <div id="italic">Kind of Contract: ${object.type_id and object.type_id.name or ''}
	            <br/>
	            From date ${date_format(object.date_start)} ${object.date_end and 'to date ' + date_format(object.date_end) or ''}</div>
	            </li>
	            <li>
	            Địa điểm làm việc: ${object.employee_id.work_location or ''}
	            <br/>
	            <div id="italic">Working place: ${object.employee_id.work_location or ''}</div>
	            </li>
	            <li>
	            <div id="content_full_no_padding">Chức vụ/chức danh chuyên môn: ${object.job_id.name or ''}</div>
	            <div id="content_full_no_padding" style="font-style: italic;">Position/Profession: ${object.job_id.name or ''}</div>
	            </li>
	            <li>
	            Mô tả công việc: Các công việc theo sự phân công của lãnh đạo Công ty
	            <br/>
	            <div id="italic">Job description: All tasks as assigned by the company's management</div>
	            </li>
	        </ol>
		</div>
		<div id="content_heading">
			Điều 2: Thời gian làm việc
			<br/>
			<div id="italic">Article 2: Working Hour</div>
		</div>
		<div id="content_full">
			Thời giờ làm việc: ${object.working_hours and object.working_hours.name or ''}
			<br/>
			<div id="italic">Working time: ${object.working_hours and object.working_hours.name or ''}</div>
	    </div>
	    <div id="content_heading">
			Điều 3: Quyền lợi và nghĩa vụ của Người lao động
			<br/>
			<div id="italic">Article 3: Obligations, right and benefit of the Employee</div>
		</div>
		<div id="content_full">
		   <ol class="list">
	            <li>
		            Quyền lợi của người lao động
		            <div id="italic">Right and benefits of the Employee</div>
		            <div id="content_full">
			            Phương tiện đi lại: Tự túc
				        <div id="italic">Mean of transportation: Self-supporting</div>
			        </div>
			        <div id="content_full">
				        Lương chính : ${formatLang(object.wage)} VND/ tháng 
				        Các khoản trợ cấp khác (mức độ phức tạp của công việc, bằng cấp, tiền ăn, xe,...) : 0 VND/ tháng
				        <div id="italic">
				        Monthly salary: ${formatLang(object.wage)} VND/month
				        Other allowances: 0 VND/month
				        </div>
			        </div>
		            <div id="content_full">
				        Tổng thu nhập sau khi trừ thuế : ${object.wage} VND
				        <div id="italic">Total income net: ${object.wage} VND</div>
			        </div>
		            <div id="content_full">
				        Hình thức trả lương: Lương được tính và được thanh toán bằng chuyển khoản/tiền mặt vào ngày 5 của tháng kế tiếp.
				        <div id="italic">Method of Payment: Salary to be calculated and paid on the fifth of the following month by Bank transfer/in cash.</div>
			        </div>
		            <div id="content_full">
				        Tăng lương: Theo Quy định của Công ty
				        <div id="italic">Salary Increment: According to the Company’s Policies</div>
			        </div>
		            <div id="content_full">
				        Thưởng: Lương tháng 13 (Được xác định tính đến ngày 31/12 hằng năm). Tuy nhiên, nhân viên sẽ không có được hưởng khoản thu nhập này nếu rời khỏi công ty trước ngày cuối cùng của tháng hai (02) của năm sau liền kề.
				        <div id="italic">Bonus: 13th month salary (defined to calculate until 31/12 yearly). The employee will not qualify for this bonus, if she/he leaves the company before the end of February of the following year.</div>
			        </div>
		            <div id="content_full">
				        Đào tạo: Theo chương trình và kế hoạch của Công ty.
				        <div id="italic">Training: According to the training schedule and plan arranged by the Company.</div>
			        </div>
		            <div id="content_full">
				        Chế độ nghỉ ngơi: Theo quy định của Công ty và pháp luật về lao động hiện hành.
				        <div id="italic">Time of Rest: According to the Company's Labor Regulation and current labor regulations.</div>
			        </div>
		            <div id="content_full">
				        Bảo hiểm xã hội và y tế: Người lao động được đóng bảo hiểm y tế và bảo hiểm xã hội đúng theo quy định của công ty.
				        <div id="italic">Social & health insurance: Social and health insurance of the Employee will be paid in accordance with the regulations on insurance of the company.</div>
			        </div>
	            </li>
	            <li>
		            Nghĩa vụ của người lao động
		            <br/>
		            <div id="italic">Obligations of the Employee</div>
		            <div id="content_full">
		                Hoàn thành công việc mình đảm trách nêu trong Hợp đồng, chấp hành lệnh điều hành sản xuất kinh doanh, bảo vệ tài sản của Công ty và sẽ chịu trách nhiệm bồi thường những tài sản bị hư hỏng do vô ý, bất cẩn hay cẩu thả hoặc bị mất cắp khi chuyển giao.
				        <br/>
				        <div id="italic">Fulfill the Job undertaken in this contract, to comply with production and business orders, protect the properties of the Company and shall compensate for damage or loss properties incurred by the Company due to carelessness, negligence or stolen.</div>
				    </div>
				    <div id="content_full">
				        Nghiêm túc tuân thủ và tôn trọng thời hạn và các cam kết trong hợp đồng. Bồi thường cho Công ty các chi phí đào tạo và/hoặc các cam kết trách nhiệm bằng tiền nêu trong Hợp đồng này hoặc trong quy định của Công ty trong trường hợp chấm dứt hợp đồng lao động trước thời hạn mà không được sự đồng ý của lãnh đạo Công ty.
				        <br/>
				        <div id="italic">Strictly follow and respect the term of and commitment in the Labor contract. Compensate to the Company all training expenses and/or monetary commitment mentioned in the Labor contract and/or in labor regulations of the Company in the case the Employee intentionally terminate the Labor contract without approval of the director of the Company.</div>
				    </div>
		            <div id="content_full">
				        Nghiêm túc tuân thủ và tôn trọng các yêu cầu của lãnh đạo, các nội quy và quy định của Công ty.
				        <br/>
				        <div id="italic">Strictly follow the instruction of management level, rules and regulations in the Company.</div>
		            </div>
	            </li>
	        </ol>
		</div>
		<div id="content_heading">
			Điều 4: Quyền và nghĩa vụ của Người sử dụng lao động
			<br/>
			<div id="italic">Article 4: Obligations and rights of the Employer</div>
		</div>
		<div id="content_full">
		   <ol class="list">
	            <li>
		            Nghĩa vụ của Người sử dụng lao động
		            <br/>    
		            <div id="italic">Obligations of the Employer</div>
		            <div id="content_full">
			            Đảm bảo việc làm và thực hiện đầy đủ các điều đã cam kết trong hợp đồng.
				        <br/>
				        <div id="italic">Ensure the work and completely fulfill all the commitment in the Contract.</div>
			        </div>
		            <div id="content_full">
				        Thanh toán đầy đủ, đúng thời hạn các chế độ và quyền lợi cho người lao động theo Hợp đồng.
				        <br/>
				        <div id="italic">Duly and in time settle all the rights and obligations to the Employee in accordance with the Contract.</div>
		            </div>
	            </li>
	            <li>
	            Quyền hạn của người sử dụng lao động
	            <div id="italic">Rights of the Employer</div>
	            <div id="content_full">
		            Có quyền đình chỉ hoặc áp dụng hình thức kỷ luật theo Luật lao động và Nội quy lao động hoặc chấm dứt Hợp đồng đối với Người lao động vi phạm nội quy, quy định của Công ty hoặc không đáp ứng các yêu cầu về sức khỏe cũng như chuyên môn.
			        <div id="italic">Has the right to suspend or apply disciplinary measures according to labor law and regulations or terminate the contract of the Employees who has violated the regulations, rule of the Company or the health and ability could not meet the requirement of work.</div>
		        </div>
	            <div id="content_full">
			        Người sử dụng lao động có quyền điều chuyển Người lao động sang nơi làm việc khác mà Người sử dụng lao động điều hành hoặc làm chủ theo quy định của pháp luật.
			        <div id="italic">Employer reserves the right to transfer the Employee to other property which is owned or managed by the Employer in accordance to the law and regulations.</div>
	            </div>
	            </li>
	        </ol>
		</div>
		<div id="content_heading">
			Điều 5: Điều khoản chung
			<br/>
			<div id="italic">Article 5: General provisions</div>
		</div>
		<div id="content_full">
		   <ol class="list">
	            <li>
		            Hợp đồng này được làm và ký ngày: ${object.date_start} tại Thành phố Hố Chí Minh
		            <br/>
		            <div id="italic">This contract is made and signed on: ${object.date_start} in Ho Chi Minh City</div>
	            </li>
	            <li>
		            Hợp đồng này được làm thành 2 bản, Người sử dụng lao động giữ 1 bản và Người lao động giữ 1 bản.
			        <br/>
			        <div id="italic">This Contract is made in 2 copies, 1 copy will be kept by the Employer and 1 copy to be kept by the Employee.</div>
	            </li>
	        </ol>
		</div>
		<div id=footer_left>
	        Người sử dụng lao động
	        <br/>
	        Employer
	        <br/>
	        ${object.employee_id.parent_id and object.employee_id.parent_id.job_id and object.employee_id.parent_id.job_id.name or ''}/${object.employee_id.parent_id and object.employee_id.parent_id.job_id and object.employee_id.parent_id.job_id.name or ''}
	    </div>
        <div id="footer_right">
	        Người lao động
	        <br/>
	         Employee
	    </div>
	    <div id=footer_left>
	       ${object.employee_id.parent_id and object.employee_id.parent_id.name}
	    </div>
	    <div id="footer_right">
	        ${object.employee_id.name}
	    </div>
	</div>
</div>
%endfor
</BODY>
</HTML>
