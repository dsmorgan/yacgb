# Yet Another Cryptocurrency Grid Bot (yacgb)

## Overview
An experiment in bot-based Crypto trading, with the goal of having it run in the cloud and having Jeff Bezos pay for running it! [^1]. The current implementation uses a standard grid trading strategy, with the ability to set several safety settings in cases that the current price of a currency goes outside of the grid. 

Built using:
- ccxt library, enabling access to just about every crypto exchange out there
- pynamodb library, enabling persistence using AWS DynamoDB

[^1]: Leveraging AWS Free-Tier, which [notoriously lacks any guardrails](https://www.lastweekinaws.com/blog/is-the-aws-free-tier-really-free/). No gurantees it will actually cost you nothing and requires fairly regular monitoring and experience in AWS cost management practices, YMMV.

---

# Install
Prerequisites:
- Python3.x (Python 3.8 is preferred, based on AWS Lambda support)
- AWS CLI (awscli v2, although v1 may work as well)

```shell
$ git clone https://github.com/dsmorgan/yacgb.git
```
The bot can be installed in different ways in AWS, as well as can be run locally.

## Deploy in AWS, using supplied helper scripts
If not setup already, configure your awscli client. At a minimum, you'll need to set your region, access key and secret.

```shell
$ aws configure

```
Use the scripts in the aws directory to build and deploy.

```shell
$ cd yacgb/aws

```
Create bucket for storing the lambda and layers.

```shell
$ ./1-create-bucket.sh
make_bucket: yacgb-e7cccc733e0f6dac

```
Build the layers, resolve and missing dependencies before moving to the next step.

```shell
$ ./2-build-layer.sh
Collecting...

```
Edit the next script, and configure the exchanges and market symbols you plan to use. To be safe, you can avoid setting the apikey, secret and (sometimes) password in the script and instead set these through the AWS console. Additional exchange and symbols can be added as needed later.

```shell
$ ./2.5-config-sm-pss.sh 

{
    "Version": 1
...
```

Navigate to the AWS "Systems Manager", then to the "Parameter Store" under the Application Management sub menu to modify or add additional values if required.

Use the next script to setup the Cloud Formation to deploy the IAM roles and Lambda application.

```shell
$ ./3-deploy.sh  
Uploading to be3a6ef10140b918018413f1a656b614  24320563 / 24320563.0  (100.00%)
Successfully packaged artifacts and wrote output template to file aws/out.yml.
Execute the following command to deploy the packaged template
aws cloudformation deploy --template-file /home/dsm/workspace/yacgb/aws/out.yml --stack-name <YOUR STACK NAME>

Waiting for changeset to be created..
Waiting for stack create/update to complete
Successfully created/updated stack - yacgb
```
You can test the syncticker configuration and invoke it once to ensure everything is working (pass it any event.json file, its contents are ignored)...

```shell
./4-invoke.sh synctickers ../events/event.json
[INFO]  2021-06-22T03:43:05.393Z                CCXT version: 1.50.59
...

"OK"
```
A snippet of the log should be shown, and the "OK" indicates a successful execution. Each execution will use the configuration defined in Parameterstore to collect ticker data for each exchange + market_symbol defined. About 2 weeks of historical data is collected for new market_symbols in order to support backtesting. 

In order to keep the synctickers running periodically, you'll need to manually create a trigger (Event Bridge) that will execute the lambda auatomatically every configured period. 1 minute is preferred, and can be done by setting the Schedule Expression to: rate(1 minute)

Currently, no ticker data is deleted so manual purging is required if necessary. However, the AWS free-tier (at time of writting) allows 25GB for free, and the ticker data is highly compressed so this isn't something of immediate concern.


## Deploy in AWS, using SAM
Work in progress


## Run Locally
For test and development purposes, the bot components can be run locally as well, with the addition of:
* use pip to satisfy dependencies locally
* Download and install from AWS a local dynamodb for development/testing purposes


**IMPORTANT:** When running locally, you need to make sure to set the environment variable to override the default location of the Dynamodb service, e.g. export DYNAMODB_HOST=http://localhost:8000. Otherwise, your awscli credentials and configuration may be used to leverage the AWS services remotely.

---

# Create an Event File that defines a Grid Bot configuration

Sample event.json

```json
{
  "exchange": "binanceus",
  "market_symbol": "XLM/USD",
  "grid_spacing": 0.02,
  "total_quote": 1000,
  "max_ticker": 0.4443,
  "min_ticker": 0.3437,
  "reserve": 0,
  "live_balance": "True",
  "start_base": 0,
  "start_quote": 3000,
  "makerfee": 0.001,
  "takerfee": 0.001,
  "feecurrency": "USD",
  "backtest_start": "20210526 19:00",
  "backtest_end": "20210528 01:00",
  "take_profit": 0.5011
}
```

The following table describes all the settings that are currently available. 


| Configuration Settings | Description |
| ----------- | ----------- |
| exchange | (required) Exchange name in ccxt format (e.g. binanceus) |
| market_symbol | (required)  Market Symbol in ccxt base_quote format (e.g. BTC_USD) |
| total_quote | (required) amount of quote currency allocated for the gbot to control |
| min_ticker | (optional) lowest ticker amount in quote currency to create the grid. This value is overridden if min_percent_start is configured | 
| min_percent_start | (optional) calculates the min_ticker value as a percent of the most recent ticker price (e.g. 0.25) | 
| max_ticker | (optional) highest ticker amount in quote currency to create the grid. This value is overridden if max_percent_start is configured |
| max_percent_start | (optional) calculates the max_ticker value as a percent of the most recent ticker price (e.g. 0.25) | 
| grid_spacing | (optional, default:0.04) the increment between grid lines. The grid is created by adding the increment percent from min_ticker to max_ticker. |
| reserve | (optional, default: 0.0) the amount of total_quote that should be reserved. Setting a small value here will reduce the chance that rounding errors, incomplete transactions, and unexpected issues result in failures |
| live_balance | (optional, default: False, backtest only) Setting to True will validate exchange account access and override start_base and start_quote values from the configured account |
| start_base | (optional, default: 0) amount of base available at init for trading |
| start_quote | (optional, defailt: 0) amount of quote available at init for trading | 
| makerfee | (optional, default: 0.0016) Trade makerfee percent for this exchange/market_symbol |
| takerfee | (optional, default: 0.0026) Trade takerfee percent for this exchange/market_symbol |
| feecurrency | (optional, default: USD) Trade fee currency for this exchange/market_symbol | 
| take_profit | (optional)  When set, if the market_symbol exceeds this price, all limit trades are canceled and no further trades are made. Must be greater then max_ticker |
| take_profit_percent_max | When set, overrides take_profit with a calculted value that is determined by multiplying this value by max_ticker |
| stop_loss | (optional)  When set, if the market_symbol drops below this price, all limit trades are canceled, all base currency intended for limit sales are aggregated to an immediate market sale and no further trades are made.  |
| stop_loss_precent_min |  When set, overrides stop_loss with a calculted value that is determined by multiplying this value by min_ticker |
| profit_protect_percent | When set, the all time high quote price of the market symbol is tracked, and if the price drops below by more then the percent comfigured, , all base currency intended for limit sales are aggregated to an immediate market sale and no further trades are made.| 
| init_market_order | (optional) Not implemented yet | 
| backtest_start | (optional, default: <now>, backtest only) Backtest start timestamp in UTC, using YYYYMMDD HH:MM format, e.g. 20210526 19:00 |
| backtest_end  | (optional, default: <now>, backtest only) Backtest end timestamp in UTC, using YYYYMMDD HH:MM format, e.g. 20210528 01:00 |
| backtest_timeframe | (optional, default: 1h, backtest only) determines what timeframe to use in backtesting (1m | 1h | 1d) |

backtest only settings are safely ignored when used for liveinit


# Backtesting
Use backtesting for experimentation and validation of different configuation settings. Since this function is dependant upon the ticker data collected from synctickers, make sure that is running periodically to keep up to date. You should have about 2 weeks of historical data to start for any exchange/market_symbol that is configured in the Parameter Store.

```shell
 ./4-invoke.sh backtest ../events/my_event.json 
7.25311553 @ 0.42735 Total: 212.50
[INFO]  2021-06-24T04:04:53.892Z        992e4816-3b82-443c-97bb-6702b8070050    [20210527 21:00] Sold 497.25311553 @ 0.42735 Total: 212.50
[INFO]  2021-06-24T04:04:53.909Z        992e4816-3b82-443c-97bb-6702b8070050    Limit Buy 497.25311553 @ 0.41897 Total: 208.33
[INFO]  2021-06-24T04:04:53.910Z        992e4816-3b82-443c-97bb-6702b8070050    [20210527 22:00] Bought 497.25311553 @ 0.41897 Total: 208.33
[INFO]  2021-06-24T04:04:53.910Z        992e4816-3b82-443c-97bb-6702b8070050    Limit Sell 497.25311553 @ 0.42735 Total: 212.50
...
[INFO]  2021-06-24T04:04:53.990Z        992e4816-3b82-443c-97bb-6702b8070050    >12 sell 0.43589 (208.33) <0/3> buybase 477.94417102 sellbase 487.50305444 [take 4.17/4.17] 212.50 None
[INFO]  2021-06-24T04:04:53.990Z        992e4816-3b82-443c-97bb-6702b8070050    Total Quote: 2583.33333 Total Base: 984.75616997 @ 0.41410 (407.79) = 2991.12
[INFO]  2021-06-24T04:04:53.990Z        992e4816-3b82-443c-97bb-6702b8070050    Transactions 18 (fees: 3.78) Profit 29.55/29.55
[INFO]  2021-06-24T04:04:53.990Z        992e4816-3b82-443c-97bb-6702b8070050    state: active
[INFO]  2021-06-24T04:04:53.990Z        992e4816-3b82-443c-97bb-6702b8070050    RUN TIME: 0:00:00.528851
[INFO]  2021-06-24T04:04:53.990Z        992e4816-3b82-443c-97bb-6702b8070050    {'gbotid': '546bb667-d4a1-11eb-ad37-9114274aa649'}
END RequestId: 992e4816-3b82-443c-97bb-6702b8070050
REPORT RequestId: 992e4816-3b82-443c-97bb-6702b8070050  Duration: 530.27 ms     Billed Duration: 531 ms Memory Size: 256 MB     Max Memory Used: 116 MB
XRAY TraceId: 1-60d40465-338a6b2b557f5cec2f31ca40       SegmentId: 6579fa2e2adf1ec4     Sampled: true

{"gbotid": "546bb667-d4a1-11eb-ad37-9114274aa649"}

```

Repeat as neceesary, modifiying settings and see how those changes impact transactions and profit.

# Running a Live Gridbot
Once satisified with a configuration you can then use the same configuration to initialize a live grid bot and begin active tradiing.

*Note* the init_market_order setting has not been implemented yet, so the account much have enough quote and base for the init to be successful. Use backtesting (using start and end times near now) to determine what the minimum amount of base and quote that are required, and manually buy/sell base if required.

```shell
 ./4-invoke.sh liveinit ../events/my_event.json 
...
{"gbotid": "cfcdcc07-d4a2-11eb-8ffc-efb2671e3833"}
```

Check the log for errors, and correct if necessary. If an issue occured before successfully completing an init, it may be necessary to manually cancel open orders that were created in the process. Take note of the gbotid that was output from the initlive (also in logs stored in Cloudwatch). The gbotid needs to be placed in the parameterstore for the liverun to discover.

In the AWS console, goto the System Manager, then the Parameter Store menu item. Edit the "/yacgb/prod/gbotids" and replace or add the gbotid to the value. This is a list value, so multiple gbotids can be configured at a time. (if running locally, the System Manager/Parameter Store settings can be set locally as environmental variables, although only a single exchange, market_symbol, and gbot can be run at a time)

You can manually run the liverun function manually to see if it works (pass it any event.json file, its contents are ignored)...

```shell
 ./4-invoke.sh liverun ../events/event.json 
...
```
Similar to synctickers, we'll want to have this function run periodically. You'll need to manually create a trigger (Event Bridge) that will execute the lambda auatomatically every configured period. 1 minute is preferred, and can be done by setting the Schedule Expression to: rate(1 minute)

That's it! Use Cloudwatch to check on status, as well as your exchange's trade interface. You should see the grid that is created, and as prices move up and down, new trades replaces old ones. 

## Stopping a Live Gridbot
1. Either stop the Event Bridge trigger AND/OR remove the gbotid(s) from the Parameter Store setting "/yacgb/prod/gbotids"
2. Using your exchange's tradeing tool, manually cancel all open orders if there are any

*Note:* currently, the Parameter Store is only read once on initiatialization of the lambda, therefore it is not deterministic when changing the "/yacgb/prod/gbotids" setting is applied with the Event Bridge trigger set. In the Lambda's configuration page, you can set a bogus environment parameter to force the Lambda to re-read Parameter Store settings. 


## Deleting and Cleanup
Use the script in the aws directory to delete the stack and cleanup most of the functions.

```shell
$ ./5-cleanup.sh
Deleted yacgb stack.
Delete deployment artifacts and bucket (yacgb-e7cccc733e0f6dac)? (y/n)y
delete: s3://yacgb-e7cccc733e0f6dac/8fe9cf785d08943d9904b5e1c82d2c23
delete: s3://yacgb-e7cccc733e0f6dac/be3a6ef10140b918018413f1a656b614
remove_bucket: yacgb-e7cccc733e0f6dac
Delete function log group (/aws/lambda/yacgb-synctickers-772VVOXEiVVr)? (y/n)y
```

Some things that yiou may need to deleted to remove all traces of this deployment:
- Cloudwatch - remove all log groups associated with the yacgb application
- System Manager - remove all the parameter store configuration starting with "/yacgb"
- DynamoDB - delete the tables: OHLCV, Gbot, Market, and Orders (if they exist)
