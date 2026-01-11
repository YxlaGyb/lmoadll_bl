use actix_web::{web, Responder, HttpRequest};
use log::{error, warn};
use crate::jwt::{generate_token, validate_token};
use crate::cookies::{create_refresh_token_cookie, create_clear_refresh_token_cookie};
use crate::middleware::response::ResponseHandler;

use crate::types::{
    login_request::LoginRequest,
    login_response::LoginData,
    token_response::TokenData,
    authenticated_user::AuthenticatedUser,
};

// 用户存储（简化实现）
static USERS: &[(&str, &str, u32, &str)] = &[
    ("admin", "password123", 1, "superadministrator"),
    ("user", "password456", 2, "user"),
];

// 登录接口
pub async fn login_api(login_req: web::Json<LoginRequest>) -> impl Responder {
    
    // 检查请求数据是否为空
    if login_req.username_email.is_empty() || login_req.password.is_empty() {
        return ResponseHandler::custom_error("邮箱和密码不能为空喵喵");
    }
    
    // 验证用户凭据
    let user = USERS.iter().find(|&&(username, _password, _, _)| {
        username == login_req.username_email
    });
    
    if let Some(&(username, password, uid, group)) = user {
        if login_req.password == password {
            // 生成access_token (60分钟过期)
            let access_token = match generate_token(uid, username, 60) {
                Ok(token) => token,
                Err(e) => {
                    error!("生成access_token失败: {}", e);
                    return ResponseHandler::custom_error("生成令牌失败喵喵");
                }
            };
            
            // 生成refresh_token (7天过期)
            let refresh_token = match generate_token(uid, username, 7 * 24 * 60) {
                Ok(token) => token,
                Err(e) => {
                    error!("生成refresh_token失败: {}", e);
                    return ResponseHandler::custom_error("生成令牌失败喵喵");
                }
            };
            
            // 设置Http-only Cookie存放refresh_token
            let refresh_cookie = create_refresh_token_cookie(&refresh_token);
            
            let login_data = LoginData {
                uid,
                name: username.to_string(),
                avatar: "".to_string(),
                group: group.to_string(),
                access_token,
            };
            
            let mut response = ResponseHandler::success(Some(login_data), "登录成功喵");
            response.add_cookie(&refresh_cookie).unwrap();
            response
            
        } else {
            custom_error_response::<()>("邮箱或密码错误喵喵", None)
        }
    } else {
        custom_error_response::<()>("邮箱或密码错误喵喵", None)
    }
}

// Token刷新接口
pub async fn refresh_token_api(req: HttpRequest) -> impl Responder {
    // 从Cookie中获取refresh_token
    let refresh_token = req.cookie("refresh_token")
        .map(|c| c.value().to_string());
    
    if let Some(token) = refresh_token {
        match validate_token(&token) {
            Ok(payload) => {
                // 生成新的access_token
                let new_access_token = match generate_token(payload.uid, &payload.name, 60) {
                    Ok(token) => token,
                    Err(e) => {
                        error!("生成新access_token失败: {}", e);
                        return error_response::<()>("令牌刷新失败喵喵", None);
                    }
                };
                
                let token_data = TokenData {
                    access_token: new_access_token,
                };
                
                success_response(Some(token_data), "令牌刷新成功喵")
            }
            Err(e) => {
                warn!("Refresh token验证失败: {}", e);
                custom_error_response::<()>("令牌无效或已过期喵喵", None)
            }
        }
    } else {
        custom_error_response::<()>("未找到刷新令牌喵喵", None)
    }
}

// 登出接口
pub async fn logout_api() -> impl Responder {
    // 清除Cookie中的refresh_token
    let clear_cookie = create_clear_refresh_token_cookie();
    
    let mut response = success_response::<()>(None, "登出成功喵");
    response.add_cookie(&clear_cookie).unwrap();
    response
}

// 受保护的路由示例
pub async fn protected_api(user: AuthenticatedUser) -> impl Responder {
    success_response(Some(user), "受保护路由访问成功喵")
}