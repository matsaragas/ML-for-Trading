This is a repo designed to explore machine learning techniques for stocks

### Fundamentals Used:

* **Market Cap**: The total value of its outstanding shares of stocks. It provides a measure 
of a company's overall worth as perceived by the stock market. 
  Market Cap is calculated as: `Market Cap = Share Price x Number of outstanding shares`,
  where outstanding share is the total number of shares currently held by 
shareholders, including institutional investors and company insiders.


* **Trailing P/E** (Price-to-Earnings Ratio) is a valuation metric that 
compares a company's current stock price to its earnings per share (EPS)
  over the past 12 months (trailing 12 months)
  `Traling PE = current stock price / EPS over the last 12 months`. It provides insights into how much investors are willing to pay each 
  for each dollar of earnings the company generated in the past. To estimate the EPS over the last 12 months,
  we sum up the net income (or profit) for each quarter to calculate the trailing 12 months' net income. We then subtract prefered 
  dividends (if the company has issued preferred share, subtract the dividends paid to those shareholders over the same 12-month period).
  Finally, we find the weighted average number of outstanding shares. For example, beginning of period: `1,000M` shares, 
  end of period: `1,100M` shares. Then, `weighted average shares = (1,000M + 1,100M)/2 = 1,050M`. So, we have,
  `EPS (TTM) = (Net Income - Preferred Dividends)/Weighted Average Shares`
  
  
* **Forward P/E** is metric that measures a company's current stock price relative to its expected earnings
per share (EPS) over the next 12 months or a specified future period. Unlike the trailing P/E, which uses
  historical earnings, the forward P/E is based on projected or forecasted earning. `Forward P/E = Current Stock Price / Estimated Future Earnings Per Share (EPS)`. 
  The estimated future EPS is the company's forecasted earnings per share, typically based on analyst estimates or company guidance. 
  A high forward P/E may indicate that investors expect significant growth in future earnings. A lower Forward P/E might signal limited growth potential or undervaluation 
  (or potentially higher risk)
  

* **PEG Ratio (Price/Earnings-to-Growth Ratio)** is a valuation metric that adjusts the traditional (P/E) by factoring in a company's 
earning growth rate. It provides a more concrete picture on whether a stock is overvalued or undervalued by considering how fast the company's earning are expected to grow.
  
  

  
