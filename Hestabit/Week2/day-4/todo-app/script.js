body {
    font-family: sans-serif;
    background-color: #f4f4f4;
    display: flex;
    justify-content: center;
    padding-top: 50px;
}

.container {
    background: white;
    padding: 20px;
    width: 400px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    padding: 10px 15px;
    cursor: pointer;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
}

ul {
    list-style: none;
    padding: 0;
}

li {
    background: #fff;
    border-bottom: 1px solid #eee;
    padding: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.btn-group {
    display: flex;
    gap: 5px;
}

.edit-btn { background-color: #ffc107; color: black; }
.delete-btn { background-color: #dc3545; }
