import AWS from "aws-sdk";
const ddb = new AWS.DynamoDB.DocumentClient();
const RATE_LIMIT = 5;
const WINDOW_SECONDS = 300;
const TABLE_NAME = "FormIPLimitTable";

export const handler = async (event) => {
  const ip = event.requestContext.http.sourceIp;
  const limitStatus = await checkAndUpdateRateLimit(ip);
  if (limitStatus.blocked) {
    return {
      statusCode: 429,
      body: JSON.stringify({
        errorMessage: "Too many requests. Try again later."
      }),
    };
  }
  console.log("IP Rate Limit Check Passed");

  const api_body = JSON.parse(event.body);
  const token = api_body.token;
  const secret_key = process.env.secret_key;

  console.log("Verifying reCAPTCHA token-" + token);
  const response = await fetch('https://www.google.com/recaptcha/api/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `secret=${secret_key}&response=${token}`
  });

  if (!response.ok) {
    const responseBody = await response.text();
    console.error('reCAPTCHA verification failed:', {status: response.status, body: responseBody});
    return {
      statusCode: response.status,
      body: JSON.stringify({
          success: false,
          errorMessage: `Failed to verify reCAPTCHA.`
      })
  };
  }

  const data = await response.json();
  if (!data.success) {
    console.error('reCAPTCHA verification failed:', data);
    return {
      statusCode: response.status,
      body: JSON.stringify({
          success: false,
          errorMessage: `reCAPTCHA verification failed. success: ${data.success}, error: ${data['error-codes']}`
      })
    };
  }
  console.log("reCAPTCHA verification succeeded! Data:" + JSON.stringify(data))
  return {
      statusCode: response.status,
      body: JSON.stringify(data)
  }
};

async function checkAndUpdateRateLimit(ip) {
  console.log("Incoming IP: " + ip);
  const now = Math.floor(Date.now() / 1000);
  const ttl = now + WINDOW_SECONDS;

  console.log(`Checking ${TABLE_NAME} Table for IP: ${ip}`);
  try {
    const result = await ddb.get({
      TableName: TABLE_NAME,
      Key: { ip },
    }).promise();

    const currentCount = result.Item?.count || 0;
    console.log("Current IP Rate: " + currentCount);
    if (currentCount >= RATE_LIMIT) {
      console.log("IP Rate Limit Exceeded: " + ip);
      return { blocked: true };
    }

    await ddb.put({
      TableName: TABLE_NAME,
      Item: {
        ip,
        count: currentCount + 1,
        ttl,
      },
    }).promise();
    console.log(`IP Rate Limit Updated to ${currentCount+1}`);
    

    return { blocked: false };
  } catch (error) {
    console.error("Rate limiting error:", {message: error.message, code: error.code, stack: error.stack});
    return { blocked: false }; // Fail open if DynamoDB error occurs
  }
}