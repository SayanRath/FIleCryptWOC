
const content= document.querySelector(".content");
const addBtn = document.querySelector('.Create');
const menu = document.getElementById('dropdownMenu');

// 1. Toggle the menu when clicking the button
addBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // Stop click from bubbling to the window
    menu.classList.toggle('show');
});

// 2. Close the menu if the user clicks anywhere else on the page
window.addEventListener('click', () => {
    if (menu.classList.contains('show')) {
        menu.classList.remove('show');
    }
});

document.getElementById('createFolder').addEventListener("click", () => {
    let Folder_Name = document.createElement("div");
    let Type = document.createElement("div");
    let Owned_By = document.createElement("div");
    let Access = document.createElement("div");
    let Actions = document.createElement("div");
    let Item = document.createElement("div");
    let Icon = document.createElement("i");

    Item.classList.add("item","list-element");
    Folder_Name.classList.add("head","FileName");
    Type.classList.add("head", "Type");
    Owned_By.classList.add("head",  "OwnedBy");
    Access.classList.add("head", "Access");
    Actions.classList.add("head", "Actions");
    Icon.classList.add("fa-solid", "fa-folder");
    

    Folder_Name.append(Icon," Folder1");
    Owned_By.innerText= "No one";
    Access.innerText= "Public";
    Type.innerText= "Folder";
    Actions.innerText= "yesterday";

    Item.append(Folder_Name,Type,Owned_By,Access,Actions);
    content.appendChild(Item);

}


)





// upload file button code

const uploadFileBtn = document.querySelector("#uploadFile");
const uploadpage = document.querySelector(".container");

uploadFileBtn.addEventListener("click", ()=>{
    uploadpage.classList.replace("diplaypopuphide","diplaypopupshow");
}

)


