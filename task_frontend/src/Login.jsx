import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import './Login.css';
import {useSpring, animated } from 'react-spring';

function Login() {
    let [username, setUsername] = useState("");
    let [password, setPassword] = useState("");
    let [message, setMessage] = useState("");
    let [errorMessage, setError] = useState("");

    const navigate = useNavigate();
    const styles= useSpring({
        from: {opacity:0, transform: 'translateY(-50px)'},
        to: {opacity:1, transform: 'translateY(0)'},
        config: {duration: 4000, friction:20, tesnsion:200},
    })

    async function login(event) {
        event.preventDefault();

        const url = 'http://127.0.0.1:8000/api/users/login';
        const data = {
            username: username,
            password: password,
        }
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { 'Content-Type': 'application/Json' },
                body: JSON.stringify(data)
            })
            const rez = await response.json();
            if (response.status === 200) {
                setMessage(rez.message);
                sessionStorage.setItem('token', rez.token);
                sessionStorage.setItem('user_id', rez.user_id);
                setTimeout(() => navigate("/home"), 2000);
            }
            else {
                setError(rez.error)
            }
        } catch (error) {
            setError('Unable to log you in at this time, kindly try again later');
            console.error(error);
        }
    }

    return (
        <>
            <div className="container">
                <div className="rightSection">
                    <animated.div style={styles}><h2>Welcome back, please sign in to continue</h2>
                    <form className="loginForm" onSubmit={login}>
                        <label htmlFor="username">Username</label><br />
                        <input required type="text" name="username" value={username} onChange={(e) => setUsername(e.target.value)}></input><br />
                        <label htmlFor="password">Password</label><br />
                        <input required type="password" name="password" value={password} onChange={(e) => setPassword(e.target.value)}></input><br />
                        <button type="submit" className="signBut">Login</button>
                    </form>
                    {errorMessage ? <p className="error">{errorMessage}</p> : <p className="success">{message}</p>}
                    <p>Don't have an account?<Link to="/">Signup</Link></p></animated.div>
                </div>
                <div className="imageBg">
                </div>
            </div>
        </>
    );
}

export default Login;