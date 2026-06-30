#how many subscribers exist
-- 
SELECT COUNT(*) AS total_subscribers
FROM utel_bi.subscriber;

#how many subscribers were acquired each month?
SELECT DATE_FORMAT(activation_date, '%Y-%m') AS month, COUNT(MSISDN) AS subscribers_acquired
FROM utel_bi.subscriber
GROUP BY DATE_FORMAT(activation_date, '%Y-%m');

#what is the subscriber growth trend?

#How many subscribers made calls?
SELECT COUNT(DISTINCT calling_msisdn) AS subscribers_with_calls
FROM utel_bi._call;

#How many subscribers sent SMS?
SELECT COUNT(DISTINCT source_msisdn) AS subscribers_with_sms
FROM utel_bi.sms;

#How many subscribers purchased airtime?
SELECT COUNT(DISTINCT msisdn) AS subscribers_with_airtime
FROM utel_bi.airtime_sale;

#How many subscribers purchased Internet?
SELECT COUNT(DISTINCT msisdn) AS subscribers_with_internet
FROM utel_bi.internet_bundle_sale;

#who are the top 10 sms users?
SELECT source_msisdn, COUNT(source_msisdn) AS sms_count
FROM utel_bi.sms
GROUP BY source_msisdn
ORDER BY sms_count DESC
LIMIT 10;   

#what is the average call duration?
SELECT AVG(duration_seconds) AS average_call_duration
FROM utel_bi._call;

#who are the top 10 callers?
SELECT calling_msisdn, COUNT(calling_msisdn) AS call_count
FROM utel_bi._call
GROUP BY calling_msisdn
ORDER BY call_count DESC
LIMIT 10;


#How much airtime revenue was generated? 
SELECT SUM(amount) AS total_airtime_revenue
FROM utel_bi.airtime_sale;

#How much fibre revenue was generated? 
SELECT SUM(monthly_fee) AS total_fibre_revenue
FROM utel_bi.fibre_subscription;

#How much voice revenue was generated? 
SELECT SUM(charge_amount) AS total_voice_revenue
FROM utel_bi._call;

#What is the total revenue? 

SELECT 
    (SELECT SUM(amount) FROM utel_bi.airtime_sale) +
    (SELECT SUM(monthly_fee) FROM utel_bi.fibre_subscription) +
    (SELECT SUM(amount) FROM utel_bi.internet_bundle_sale) +
    (SELECT SUM(charge_amount) FROM utel_bi._call) AS total_revenue;




