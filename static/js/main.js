const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
function toast(msg,ok=true){const t=document.createElement('div');t.className=`alert alert-${ok?'success':'danger'} shadow`;t.textContent=msg;$('.toast-wrap').append(t);setTimeout(()=>t.remove(),5000)}
const loader=on=>$('#loader').classList.toggle('on',on);
async function api(url,method,body){loader(true);try{const r=await fetch(url,{method,headers:{'Content-Type':'application/json'},body:body&&JSON.stringify(body)});return await r.json()}catch(e){return{ok:false,message:'Network error. Try again.'}}finally{loader(false)}}
$$('form[data-api]').forEach(f=>f.addEventListener('submit',async e=>{e.preventDefault();f.classList.add('was-validated');if(!f.checkValidity())return;
 const res=await api(f.dataset.api,f.dataset.method||'POST',Object.fromEntries(new FormData(f)));
 toast(res.message,res.ok);if(!res.ok)return;
 if(f.dataset.confirm){f.classList.add('d-none');$('#confirm').classList.remove('d-none');$('#confirm-msg').textContent=res.message;scrollTo({top:0,behavior:'smooth'})}
 else if(res.redirect)setTimeout(()=>location=res.redirect,600);else if(f.dataset.reset!==undefined){f.reset();f.classList.remove('was-validated')}}));
$$('[data-post]').forEach(b=>b.addEventListener('click',async()=>{const r=await api(b.dataset.post,'POST',b.dataset.body&&JSON.parse(b.dataset.body));toast(r.message,r.ok);if(r.redirect)setTimeout(()=>location=r.redirect,500);if(r.reload)setTimeout(()=>location.reload(),500)}));
const dq=$('#docSearch'),ds=$('#docDept');
if(dq){const go=()=>{const t=dq.value.toLowerCase(),d=ds.value;let n=0;$$('.doc').forEach(c=>{const s=(!d||c.dataset.dept===d)&&c.dataset.name.includes(t);c.classList.toggle('d-none',!s);n+=s});$('#docEmpty').classList.toggle('d-none',n>0)};dq.oninput=ds.onchange=go}
const ad=$('#apptDept'),adoc=$('#apptDoc'),adate=$('#apptDate'),aslot=$('#apptSlot');
if(ad){adate.min=new Date().toISOString().slice(0,10);
 const loadSlots=async()=>{if(!adoc.value||!adate.value)return;const r=await(await fetch(`/api/slots?doctor=${adoc.value}&date=${adate.value}`)).json();aslot.innerHTML='<option value="">Select time slot</option>'+r.map(s=>`<option>${s}</option>`).join('');if(!r.length)toast('No free slots on that date. Try another day.',false)};
 const loadDocs=async pre=>{const r=await(await fetch('/api/doctors?dept='+ad.value)).json();adoc.innerHTML='<option value="">Select doctor</option>'+r.map(d=>`<option value="${d.id}">${d.name}</option>`).join('');if(pre)adoc.value=pre;loadSlots()};
 ad.onchange=()=>loadDocs();adoc.onchange=adate.onchange=loadSlots;
 if(ad.dataset.pre){ad.value=ad.dataset.pre;loadDocs(ad.dataset.doc)}}
