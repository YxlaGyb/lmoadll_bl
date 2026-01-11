use actix_web::{http::StatusCode, HttpResponse, Responder};
use serde::{Deserialize, Serialize};


// 定义类型
#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum JsonValue {
    String(String),
    Number(f64),
    Bool(bool),
    Object(serde_json::Map<String, serde_json::Value>),
    Array(Vec<serde_json::Value>),
    Null,
}


// 响应结构体
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub code: u16,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
}


// 中间件自动封装
impl<T: Serialize> Responder for ApiResponse<T> {
    type Body = actix_web::body::BoxBody;

    fn respond_to(self, _req: &actix_web::HttpRequest) -> HttpResponse<Self::Body> {
        let status = StatusCode::from_u16(self.code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR);
        HttpResponse::build(status).json(self)
    }
}


// 响应工厂
pub struct ResponseHandler;

impl ResponseHandler {
    const SUCCESS_CODE: u16 = 200;
    const CUSTOM_ERROR_CODE: u16 = 233;
    const ERROR_CODE: u16 = 500;

    pub fn success<T: Serialize>(data: T) -> ApiResponse<T> {
        ApiResponse {
            code: Self::SUCCESS_CODE,
            message: "OK".to_string(),
            data: Some(data),
        }
    }

    pub fn custom_error(msg: &str) -> ApiResponse<()> {
        ApiResponse {
            code: Self::CUSTOM_ERROR_CODE,
            message: msg.to_string(),
            data: None,
        }
    }

    pub fn error(msg: &str) -> ApiResponse<()> {
        ApiResponse {
            code: Self::ERROR_CODE,
            message: msg.to_string(),
            data: None,
        }
    }
}

// #[get("/ok")]
// async fn index() -> impl Responder {
//     // 返回 dict 模式
//     let mut data = serde_json::Map::new();
//     data.insert("user_id".to_string(), serde_json::json!(1001));
    
//     ResponseHandler::success(data)
// }

// #[get("/error")]
// async fn fail() -> impl Responder {
//     ResponseHandler::custom_error("账户余额不足")
// }

// #[actix_web::main]
// async fn main() -> std::io::Result<()> {
//     HttpServer::new(|| {
//         App::new()
//             .service(index)
//             .service(fail)
//     })
//     .bind(("127.0.0.1", 8080))?
//     .run()
//     .await
// }
