const Submit1 = document.getElementById("Submitform");
URL="http://127.0.0.1:8000"
import { userName } from "./userName.1.js";

let token;
let User_name;
const userData = {
        name: null,
        email: null,
        password: null,
    };

let Verify =  async (e) => { 
    e.preventDefault();
    const MFACode = document.querySelector("#MFA").value;
    let check = await fetch(`${URL}/verify-mfa?email=${userData.email}&user_provided_code=${MFACode}`,{method: 'POST'});
    userData.name="";
    userData.email="";
    userData.password="";
    let status= await check.json();
    console.log(status["state"]);
    if( status["state"] === "Session Ended (Timed Out)" ){
        
        window.location.reload();
        let btn2 = document.getElementById("Verify");
        btn2.remove();
    }
    else if (status["state"] === "Wrong KEY"){

        const line = document.getElementsByClassName("MFA");
        line.innerText = "Wrong Code";
    }
    else{
        window.location.href = status["state"];
    }
}

let Username_confirm = async (e)=> {
    e.preventDefault();
    userData.name= document.getElementById("Username").value;
    console.log(userData.name);
    let Response = await fetch(`${URL}/initiate-mfa`, {method: 'POST',
        headers: {
                "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
    });
    
    Response.json().then((res) => {
        const space = document.querySelector(".space");
        space.innerHTML = "";
        const btn2= document.createElement("button");
        btn2.id= "Verify"
        btn2.innerText = "Verify"
        const label = document.createElement("label");
        label.classList.add("MFA");
        label.classList.add("login");
        const p = document.createElement("p");
        p.textContent = "Enter your MFA code: ";
        const input = document.createElement("input");
        input.type = "text";
        input.id = "MFA";
        input.name = "MFA";
        label.appendChild(p);     
        label.appendChild(input);
        space.appendChild(label);
        btn2.addEventListener("click", Verify);
        space.appendChild(btn2);

} )
}
Submit1.addEventListener("click", async (e) =>{
    e.preventDefault();
    userData.password= document.getElementById("password").value;
    userData.email= document.getElementById("email").value;
    const space = document.querySelector(".space");
   
    userData.name="none";
    const existence =await fetch(`${URL}/check`, {method: 'POST',
        headers: {
                "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
    });
    const result_of_existence = await existence.json();

    if(result_of_existence["existence"]==="true"){
        
        if(result_of_existence["pswd_match"]==="true"){
            window.location.href = "home.html";
            token = result_of_existence["token"];
            User_name= result_of_existence["Username"];
            userName.innertext= "Hey! "+User_name;
            console.log(User_name);
        }
    }
    else{
         space.innerHTML = "";
        Submit1.remove();
        let Submit2 = document.createElement("button");
        Submit2.innerText = "Submit";
        Submit2.id="Submit2";
        const label = document.createElement("label");
        label.classList.add("Username");
        label.classList.add("login");
        const p = document.createElement("p");
        p.textContent = "Enter your Username: ";
        const input = document.createElement("input");
        input.type = "text";
        input.id = "Username";
        input.name = "Username";
        label.appendChild(p);     
        label.appendChild(input);
        space.append(label,Submit2);
        Submit2.addEventListener("click", Username_confirm);
    }
}); 





