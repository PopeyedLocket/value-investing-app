from libraries_and_constants import *

QUERY_YAHOO_FINANCE = True

''' TO DO

	normalize metrics
	
		fix/verify correctness of volitility and velocity and value metrics

			compare/eyeball plot_stock_data.py to the log outputs of the
			volitility and velocity and value metrics

			ex: ticker=NEE
				book_value weighted average velocity = 0.076376
				book_value weighted average volitility = 0.064624

				note:
					these are percentages, so multiple them by 100 to get to the weighted
					average percent changes/deviation (aka velocity/volitility)

				book_value for NEE looks good, verify it for the other stocks too
					python plot_stock_data.py -x <ticker>

			i should probably create a metric for "value" for net_income, book_value,
				price, dividend_paid, and dividend_yield values are all positive or zero by their nature
				so just net_income and book_value

		side notes:

			keep QUERY_YAHOO_FINANCE set to True
			see ToDo of main NOTES.txt as to why
				Ctrl F: "i updated driver.py to collect dividendYield as well"

			i created rank_stocks_OLD.py which doesn't normalize the metrics incase this fucks up too hard

	dividend dates are fucking up
		its because each row in the dividend df has a date and some stocks have sporadic time intervals between the dates
		one possible solution is to divide the percent change divided by the number of days (to get percent change per day, aka the slope)
		and then use that for velocity
			would that account for if a company skipped it for a long time then paid a big one?

			what am i looking for in a dividend?
				im looking for it to be on regular intervals (weekly, monthly, quarterly, bi-annually, or annually)
					allowing for companies that occationally provide a special dividend
				im looking for it to have fast steady growth as well

	how are price velocity and volitility scores going to be found from the weighted averages?
		answer: all interval values for average velocity and volitility are storedin the
			the df stock_df, they are then normalized on a scale of -1 to 1,
			and then the weighted average is taken to find the final value

	make plot show
		for each time interval (on a 2x2 plt grid)
			price over time
			each of the percent changes on this interval
				as a straignt line starting at the price at the beginning of each time interval
			average percent change
				as a straight line from the beginning to the end of the entire plot
			and show the weight for this one in the subplot title
		and also show a similar plot with
			price data
			the weighted average percent change of all the average percent change of each interval 
				as a line from begining to end of the entire price chart

		... how could variance be incorporated into this too?

	maybe make something for acceleration too
		and the variance of the acceleration?
		if its a stable acceleration then its acceleration, not volitility

	idea:
		could the velocity be better calculated by looking at the percent change from the current 
		point in time to each point in the past for a long time interval of 5 to 10 years.
		Weight the long term velocity higher than the short term velocity to get a good picture

			velocity = percent change / window duration in days

			perhaps they could be weighted equally as well? and still favor long term growth?

	'''
''' Description:

	strategy 3:

		for each stock s:
			look at the price data and the dividend history
			price long term slope and volitility
			dividend slope and volitility
			current dividend yield
		record these metrics for each stock
		based on the weights for each metric create a ranking of all the stocks

	seeking
		"fast steady growth
			velocity  = the weighted average percent change in price for multiple time intervals (long term
				weighted stronger) "seeking this value to be high, aka fast"
			volitility = the weighted average variance of each percent change in price (relative to the avg pct
				change used to determine velocity) for multiple time intervals (long term weighted stronger)
				"seeking this value to be low, aka "stable""
			"

		for each time interval i:

			each of the time windows needs to be weighted equally so that stocks with
			consecultive growth in all time scales is prioritized
				infact its probably even better to weight the long term time windows are weighted stronger
				stronger
				than the short term values

		on what time interval though?

		do same thing for dividend and bookvalue
		for dividend make sure it accounts for dividends on variable time values
		for dividend yield im seeking the yield itself to be a high percent value as well
		perhaps with price to book as well (but seeking lower?)
		perhaps for price im seeking the most recent percent change to be down

	run with:

		python rank_stocks.py

		note:
			the script is most accurate if its ran right after the data is collected.
			this is because the dividend yield is calculated by comparing the dividend
			per share history of the most recent year to the most recent price, and the
			"most recent" of each is from the data thats been collected, not from
			yahoo finance. The other fundamental data used in the ranking is also
			from the data collected.

	'''



decimal_to_percent_string = lambda v : '%.3f%%' % (100.0*v)

def get_velocity_and_volitility_of_price(
	daily_price_history,
	verbose=False,
	num_indents=0,
	new_line_start=False):

	# metrics = strategy_config['metrics']
	# use_window_period = strategy3['use_window_period']
	time_interval_weights = strategy_config['price_time_interval_weights']
	price_data = {'velocity' : {}, 'volitility' : {}}
	num_intervals = len(time_interval_weights.keys())
	if verbose:
		log.print('price data:', num_indents=num_indents, new_line_start=new_line_start)
		log.print('calculating average velocity and deviation (aka volitility) of data using %d time interval(s):' % num_intervals,
			num_indents=num_indents+1)
	for i, (interval, weight) in enumerate(time_interval_weights.items()):
		data = get_data_on_interval(daily_price_history.copy(), interval)
		if strategy_config['use_window_period']:
			data = data.iloc[-(strategy_config['window_period'] + 1):] # +1 because pct_change() has a nan at the beginning
		pct_changes = data['Close'].pct_change()
		pct_changes = pd.DataFrame({
			'Date'    : data['Date'],
			'decimal' : pct_changes,
			'percent' : pct_changes.apply(decimal_to_percent_string)}).iloc[1:]
		average_velocity = pct_changes['decimal'].mean() # non weighted
		deviations = pct_changes['decimal'].apply(lambda v : abs(v - average_velocity))
		average_deviation = deviations.mean() # non weighted
		if verbose:
			log.print('interval %d of %d: \"%s\"' % (
				i+1, num_intervals, interval),
				num_indents=num_indents+2)
			log.print('weight:      %.1f %%' % (
				100.0*weight),
				num_indents=num_indents+3)
			log.print('time_window: %s' % (
				'all time' if not strategy_config['use_window_period'] else (
					'past %d %s(s)' % (strategy_config['window_period'], interval))),
				num_indents=num_indents+3)
			log.print('data:', num_indents=num_indents+3)
			log.print(data.to_string(max_rows=10), num_indents=num_indents+4)
			log.print('pct_changes:', num_indents=num_indents+3)
			log.print(pct_changes.to_string(max_rows=10), num_indents=num_indents+4)
			log.print('average_velocity:', num_indents=num_indents+3)
			log.print('decimal: %s' % average_velocity, num_indents=num_indents+4)
			log.print('percent: %s' % decimal_to_percent_string(average_velocity),
				num_indents=num_indents+4)
			log.print('average_deviation', num_indents=num_indents+3)
			log.print('decimal: %s' % average_deviation, num_indents=num_indents+4)
			log.print('percent: %s' % decimal_to_percent_string(average_deviation),
				num_indents=num_indents+4)
		price_data['velocity'][interval]   = average_velocity
		price_data['volitility'][interval] = average_deviation
	if verbose:
		log.print('values of each time intervals\' average velocity and deviation:',
			num_indents=num_indents+1)
		price_data_percent = {}
		for k, v in price_data.items():
			price_data_percent[k] = {}
			for interval, value in v.items():
				price_data_percent[k][interval] = decimal_to_percent_string(value)
		log.print(json.dumps(price_data_percent, indent=4), num_indents=num_indents+2)
	for x in ['velocity', 'volitility']:
		weighted_average_x = sum(
			[price_data[x][interval] * weight \
				for i, (interval, weight) in \
				enumerate(time_interval_weights.items())])
		price_data[x]['weighted_average'] = weighted_average_x
	if verbose:
		log.print('price   velocity weighted_average: %s' % price_data['velocity']['weighted_average'],   num_indents=num_indents+1)
		log.print('price volitility weighted_average: %s' % price_data['volitility']['weighted_average'], num_indents=num_indents+1)
	return price_data
def get_velocity_and_volitility_of_fundamental_metric(
	metric_str,
	metric_col,
	metric_history,
	verbose=False,
	num_indents=0,
	new_line_start=False):

	# metrics = strategy_config['metrics']
	# use_window_period = strategy3['use_window_period']
	time_interval_weights = strategy_config['fundamentals_time_interval_weights']
	metric_data = {'velocity' : {}, 'volitility' : {}}
	num_intervals = len(time_interval_weights.keys())
	if verbose:
		log.print('%s data:' % metric_str, num_indents=num_indents, new_line_start=new_line_start)
		log.print('calculating average velocity and deviation (aka volitility) of %s data using %d time interval(s):' % (
			metric_str, num_intervals), num_indents=num_indents+1)
	for i, (interval, weight) in enumerate(time_interval_weights.items()):
		data = get_data_on_interval(metric_history.copy(), interval)
		if strategy_config['use_window_period']:
			data = data.iloc[-(strategy_config['window_period'] + 1):] # +1 because pct_change() has a nan at the beginning
		pct_changes = data[metric_col].pct_change().fillna(0).replace(np.inf, 1.0)
		pct_changes = pd.DataFrame({
			'Date'    : data['Date'],
			'decimal' : pct_changes,
			'percent' : pct_changes.apply(decimal_to_percent_string)}).iloc[1:]
		average_velocity = pct_changes['decimal'].mean() # non weighted
		deviations = pct_changes['decimal'].apply(lambda v : abs(v - average_velocity))
		average_deviation = deviations.mean() # non weighted
		if verbose:
			log.print('interval %d of %d: \"%s\"' % (
				i+1, num_intervals, interval),
				num_indents=num_indents+2)
			log.print('weight:      %.1f %%' % (
				100.0*weight),
				num_indents=num_indents+3)
			log.print('time_window: %s' % (
				'all time' if not strategy_config['use_window_period'] else (
					'past %d %s(s)' % (strategy_config['window_period'], interval))),
				num_indents=num_indents+3)
			log.print('data:', num_indents=num_indents+3)
			log.print(data.to_string(max_rows=10), num_indents=num_indents+4)
			log.print('pct_changes:', num_indents=num_indents+3)
			log.print(pct_changes.to_string(max_rows=10), num_indents=num_indents+4)
			log.print('average_velocity:', num_indents=num_indents+3)
			log.print('decimal: %s' % average_velocity, num_indents=num_indents+4)
			log.print('percent: %s' % decimal_to_percent_string(average_velocity),
				num_indents=num_indents+4)
			log.print('average_deviation', num_indents=num_indents+3)
			log.print('decimal: %s' % average_deviation, num_indents=num_indents+4)
			log.print('percent: %s' % decimal_to_percent_string(average_deviation),
				num_indents=num_indents+4)
		metric_data['velocity'][interval]   = average_velocity
		metric_data['volitility'][interval] = average_deviation
	if verbose:
		# log.print('values and weighted average of each time intervals\' average velocity and deviation:',
		log.print('values of each time intervals\' average velocity and deviation:',
			num_indents=num_indents+1)
		metric_data_percent = {}
		for k, v in metric_data.items():
			metric_data_percent[k] = {}
			for interval, value in v.items():
				metric_data_percent[k][interval] = decimal_to_percent_string(value)
		log.print(json.dumps(metric_data_percent, indent=4), num_indents=num_indents+2)
	for x in ['velocity', 'volitility']:
		weighted_average_x = sum(
			[metric_data[x][interval] * weight \
				for i, (interval, weight) in \
				enumerate(time_interval_weights.items())])
		metric_data[x]['weighted_average'] = weighted_average_x
	if verbose:
		log.print('%s   velocity weighted average: %s' % (metric_str, metric_data['velocity']['weighted_average']),   num_indents=num_indents+1)
		log.print('%s volitility weighted average: %s' % (metric_str, metric_data['volitility']['weighted_average']), num_indents=num_indents+1)
	return metric_data
def get_data_on_interval(
	df,
	interval):

	most_recent_date_str = df['Date'].iloc[-1]
	most_recent_date = datetime.strptime(most_recent_date_str, '%Y-%m-%d')
	if interval == 'day':
		pass
	elif interval == 'week':
		df['datetime'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
		df['weekday'] = df['datetime'].dt.weekday
		df = df[df['weekday'] == most_recent_date.weekday()].copy()
		df.drop(columns=['datetime', 'weekday'], inplace=True)
	elif interval == 'month':
		df = closest_month_day(df, most_recent_date)
	elif interval == 'quarter':
		df = closest_quarter_day(df, most_recent_date)
	elif interval == 'year':
		df = closest_year_day(df, most_recent_date)
	return df
def closest_month_day(df, most_recent_date):
	# this function will get a value for each month in the data thats closest to the current day of the month of today
	# this is required because the data is often not on daily intervals (ex: price data is only on workdays)
	df2 = pd.DataFrame(columns=df.columns)
	years = list(set(map(lambda d : d[:4], df['Date'].tolist())))
	years.sort()
	def get_current_day(y, m, most_recent_date):
		d = most_recent_date.day
		m = int(m)
		y = int(y)
		days_in_months = {
			1  : 31,
			2  : 28,
			3  : 31,
			4  : 30,
			5  : 31,
			6  : 30,
			7  : 31,
			8  : 31,
			9  : 30,
			10 : 31,
			11 : 30,
			12 : 31
		}
		if d > days_in_months[m]:
			d = days_in_months[m]
		return datetime(y, m, d)
	for y in years:
		df_of_y = df[df['Date'].str[:4] == y]
		months = list(set(map(lambda d : d[5:7], df_of_y['Date'].tolist())))
		months.sort()
		for m in months:
			df_of_m = df[df['Date'].str[:7] == '%s-%s' % (y, m)]
			current_day = get_current_day(y, m, most_recent_date)
			i = 1
			max_i = 30 # only add a row for this month if it has data thats within max_i of the current day, this is only used on the first month/year
			b = True
			while True:

				# days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
				# print(days[current_day.weekday()], current_day.strftime('%Y-%m-%d'))
				x = df_of_m[df_of_m['Date'] == current_day.strftime('%Y-%m-%d')]
				# print(x)
				# input()

				if not x.empty:
					df2 = df2.append(x)
					break
				else:
					current_day += timedelta(days=((1 if b else -1) * i))
					b = not b
					i += 1
					if i > max_i: break
	return df2
def closest_quarter_day(df, most_recent_date):
	# this function will get a value for each quarter in the data thats closest to the current day of the quarter of today
	# this is required because the data is often not on daily intervals (ex: price data is only on workdays)
	df['quarter'] = df['Date'].apply(lambda d : ((int(d[5:7])-1)//3)+1)
	df2 = pd.DataFrame(columns=df.columns)
	years = list(set(map(lambda d : d[:4], df['Date'].tolist())))
	years.sort()
	def get_current_day(y, q, most_recent_date):
		d = most_recent_date.day
		m = int(3*(q-1) + ((most_recent_date.month - 1) % 3) + 1)
		y = int(y)
		days_in_months = {
			1  : 31,
			2  : 28,
			3  : 31,
			4  : 30,
			5  : 31,
			6  : 30,
			7  : 31,
			8  : 31,
			9  : 30,
			10 : 31,
			11 : 30,
			12 : 31
		}
		if d > days_in_months[m]:
			d = days_in_months[m]
		return datetime(y, m, d)
	# print('most_recent_date', most_recent_date)
	for y in years:
		df_of_y = df[df['Date'].str[:4] == y]
		# print('\ny', y)
		# print('df_of_y')
		# print(df_of_y)
		quarters = list(set(df_of_y['quarter'].tolist()))
		for q in quarters:
			# print('\nq', q)
			df_of_q = df_of_y[df_of_y['quarter'] == q]
			# print('df_of_q')
			# print(df_of_q)
			current_day = get_current_day(y, q, most_recent_date)
			# print('current_day', current_day)
			i = 1
			max_i = 90 # only add a row for this month if it has data thats within max_i of the current day, this is only used on the first month/year
			b = True
			while True:

				# days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
				# print(days[current_day.weekday()], current_day.strftime('%Y-%m-%d'))
				# print('cday', current_day)
				x = df_of_q[df_of_q['Date'] == current_day.strftime('%Y-%m-%d')]
				# print(x)
				# input()

				if not x.empty:
					df2 = df2.append(x)
					break
				else:
					current_day += timedelta(days=((1 if b else -1) * i))
					b = not b
					i += 1
					if i > max_i: break
			# print('df2')
			# print(df2)
	return df2
def closest_year_day(df, most_recent_date):
	# this function will get a value for each year in the data thats closest to the current day and month of today
	# this is required because the data is often not on daily intervals (ex: price data is only on workdays)
	df2 = pd.DataFrame(columns=df.columns)
	years = list(set(map(lambda d : d[:4], df['Date'].tolist())))
	years.sort()
	for y in years:
		df_of_y = df[df['Date'].str[:4] == y]
		# print('\ndf_of_y')
		# print(df_of_y)
		current_day = datetime(int(y), most_recent_date.month, most_recent_date.day)
		i = 1
		max_i = 365 # only add a row for this year if it has data thats within max_i of the current month and day, this is only used on the first year
		b = True
		while True:

			# days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
			# print(days[current_day.weekday()], current_day.strftime('%Y-%m-%d'))
			x = df_of_y[df_of_y['Date'] == current_day.strftime('%Y-%m-%d')]
			# print('current_day', current_day)
			# print(x)
			# input()

			if not x.empty:
				df2 = df2.append(x)
				break
			else:
				current_day += timedelta(days=((1 if b else -1) * i))
				b = not b
				i += 1
				if i > max_i: break
		# print('\ndf2')
		# print(df2)
	return df2

def get_book_value_history(df):
	df['book_value'] = df['total_assets'] - df['total_liabilities']
	df.rename(columns={'sub_qtr_enddate' : 'Date'}, inplace=True)
	df = df[['Date', 'book_value']]
	return df
def get_net_income_history(df):
	df.rename(columns={'sub_qtr_enddate' : 'Date'}, inplace=True)
	df = df[['Date', 'net_income']]
	return df
def get_dividends_paid_history(df):
	df.rename(columns={'sub_qtr_enddate' : 'Date'}, inplace=True)
	df = df[['Date', 'dividends_paid']]
	return df
def get_dividend_yield(
	i, n, info,
	verbose=False,
	num_indents=0,
	new_line_start=False):

	if verbose:
		log.print('getting dividend_yield for stock %d of %d, ticker=%s, CIK=%s' % (i, n, ticker, cik),
			num_indents=num_indents, new_line_start=new_line_start)
	dividend_yield_data = {}
	if QUERY_YAHOO_FINANCE:
		if verbose:
			log.print('querying yahoo finance for dividend_yield', num_indents=num_indents+1)
		try:
			time.sleep(1)
			yf_company = yf.Ticker(ticker)
			try:
				time.sleep(1)
				yf_info = yf_company.info
				if verbose:
					log.print('successfully queried yahoo finance for yf_info', num_indents=num_indents+2)
				# print(json.dumps(yf_info, indent=4))
				key = 'dividendYield'
				if key in yf_info.keys():
					if verbose:
						log.print('successfully found current dividend_yield', num_indents=num_indents+2)
					query_successful = True
					dividend_yield = yf_info[key]
				else:
					if verbose:
						log.print('key: \"dividendYield\" not found in yf_info', num_indents=num_indents+2)
					query_successful = False
			except Exception as e:
				if verbose:
					log.print('failed to query yahoo finance for yf_info', num_indents=num_indents+2)
					log.print(e, num_indents=num_indents+3)
				query_successful = False
		except Exception as e:
			if verbose:
				log.print('failed to query yahoo finance for yf_company', num_indents=num_indents+2)
				log.print(e, num_indents=num_indents+3)
			query_successful = False

	if (not QUERY_YAHOO_FINANCE) or (not query_successful):
		if verbose:
			log.print('getting dividend_yield from info.json', num_indents=num_indents+1)
		dividend_yield = None # info['dividend_yield']
		# # calculate dividend yield from past years dividends and current price
		# current_price = daily_price_history['Close'].iloc[-1]
		# current_date = daily_price_history['Date'].iloc[-1]
		# current_date_minus_one_year = '%s%s' % (
		# 	int(current_date[:4]) - 1,
		# 	current_date[4:])
		# # print(current_date_minus_one_year)
		# # print(current_date)
		# # print(dividend_per_share_history)
		# df = dividend_per_share_history[dividend_per_share_history['Date'].between(
		# 	current_date_minus_one_year, current_date)]
		# # print(df)
		# # print(current_price)
		# dividends_of_past_year = df['Dividends'].sum()
		# # print(dividends_of_past_year)
		# dividend_yield = dividends_of_past_year / current_price
		# # print(dividend_yield)
		# return dividend_yield
	dividend_yield_data['value'] = (100 * dividend_yield) if dividend_yield != None else 0.0
	if verbose:
		log.print('done, dividend_yield = %.2f %%' % dividend_yield_data['value'],
			num_indents=num_indents)
	return dividend_yield_data

####################### unused, old strategies ###########################

def get_quadratic_slope_and_volitility(x, x_labels, y, ticker, show_plots=False):

	# line of best fit: i want the line of best fit to be either linear, or curving at most 1 time
	# no "s" shaped lines with 2 curves or squiggly shaped lines with more than 2 curves.
	# So using a quadratic equation
	# https://www.statology.org/quadratic-regression-python/
	coefficients = np.polyfit(x, y, 2)
	# print(coefficients)
	model = np.poly1d(coefficients)
	line_of_best_fit = model(x)

	# price slope: the slope of the line of best fit at this current point in time
	slope = 'tbd'

	# price volitility: the (sum from t=0 to t_max of the absolute value of the percent change between the
	# price at time t and the value of the line of best fit at time t) / number of timesteps
	volitility = sum([abs((y[t] - line_of_best_fit[t]) / y[t]) for t in x]) / float(len(x))

	if show_plots:
		s = str(model).split('\n')[-1].split('x')
		s[0], s[1] = s[0][0:-2]+'*', '^2'+s[1][0:-2]+'*'
		equation_str = 'x'.join(s)
		fig, ax = plt.subplots()
		ax.plot(x, y, c='b')
		ax.plot(x, line_of_best_fit, c='r')
		ax.set_title('ticker: %s\nline_of_best_fit: %s\nvolitility: %s' % (
			ticker, equation_str, volitility))

		ax.set_xlabel('Quarters')
		num_labels_to_display   = 5
		label_x_loc_to_display  = np.linspace(
			x[0], x[-1], num_labels_to_display).astype(int)
		labels_to_display = [x_labels[t] for t in label_x_loc_to_display]
		ax.set_xticks(label_x_loc_to_display)
		# https://stackoverflow.com/questions/14852821/aligning-rotated-xticklabels-with-their-respective-xticks
		ax.set_xticklabels(labels_to_display, rotation=45, ha='right', rotation_mode='anchor')
		fig.tight_layout()
		plt.show()

	return slope, volitility
def get_sma_slope_and_std_dev(x, x_labels, y, ticker, show_plots=False, period=200):

	# line of best fit: i want the line of best fit to be the SMA (simple moving average)
	# using a default trailing window of 200 days
	# line_of_best_fit = pd.Series(y).rolling(period).mean()
	line_of_best_fit = []
	for t in range(len(x)):
		# print(y[:t+1])
		# input()
		s, tot_w = 0, 0
		for w in range(1, t+1):
			s += y[w-1]*w*w
			tot_w += w*w
		p = s / (tot_w if tot_w != 0 else 1)
		line_of_best_fit.append(p)
	# print(line_of_best_fit)
	line_of_best_fit = pd.Series(line_of_best_fit)
	# price slope: the slope of the line of best fit at this current point in time
	slope = (line_of_best_fit.values[-1] - line_of_best_fit.values[-2]) / line_of_best_fit.values[-2]
	# slope = pd.Series(np.gradient(line_of_best_fit), line_of_best_fit.index, name='slope')

	# price volitility: the std deviation of the price around the line of best fit (using the same trailing window)
	volitility_series = pd.Series(y).rolling(period).std()
	volitility = volitility_series.values[-1] / line_of_best_fit.values[-1]

	# print(slope)
	# print(volitility)
	# sys.exit()

	if show_plots:
		fig, ax = plt.subplots()
		ax.plot(x, y, c='b')
		ax.plot(x, line_of_best_fit, c='r')
		# ax.plot(x, volitility_series, c='g')
		# ax.plot(x, line_of_best_fit + volitility_series, c='g')
		# ax.plot(x, line_of_best_fit - volitility_series, c='g')
		ax.set_title('ticker: %s' % (ticker))

		ax.set_xlabel('Quarters')
		num_labels_to_display   = 5
		label_x_loc_to_display  = np.linspace(
			x[0], x[-1], num_labels_to_display).astype(int)
		labels_to_display = [x_labels[t] for t in label_x_loc_to_display]
		ax.set_xticks(label_x_loc_to_display)
		# https://stackoverflow.com/questions/14852821/aligning-rotated-xticklabels-with-their-respective-xticks
		ax.set_xticklabels(labels_to_display, rotation=45, ha='right', rotation_mode='anchor')
		fig.tight_layout()
		plt.show()

	return slope, volitility	

def get_price_stats(df, ticker, verbose=False, show_plots=False):
	if verbose:
		log.print('daily_price_data:', num_indents=1, new_line_start=True)
		log.print(df.to_string(max_rows=6), num_indents=1)
	time_span = df.index.tolist()
	dates     = df['Date'].tolist()
	prices    = df['Close'].tolist()
	# price_slope, price_volitility = get_slope_and_volitility1(
	# 	time_span, dates, prices, ticker, show_plots=show_plots)
	price_slope, price_volitility = get_sma_slope_and_std_dev(
		time_span, dates, prices, ticker, show_plots=show_plots, period=200)
	return price_slope, price_volitility
def get_dividend_stats(df, ticker, verbose=False, show_plots=False):
	if verbose:
		log.print('dividend_per_share_history:', num_indents=1, new_line_start=True)
		log.print(df.to_string(max_rows=6), num_indents=1)
	time_span = df.index.tolist()
	dates     = df['Date'].tolist()
	dividends = df['Dividends'].tolist()
	# dividend_slope, dividend_volitility = get_slope_and_volitility1(
	# 	time_span, dates, dividends, ticker, show_plots=show_plots)
	dividend_slope, dividend_volitility = get_sma_slope_and_std_dev(
		time_span, dates, dividends, ticker, show_plots=show_plots, period=200)
	return dividend_slope, dividend_volitility

###########################################################################



if __name__ == '__main__':

	verbose = args.verbose

	# init stock_df columns
	metric_columns = []
	for k, v in strategy_config['metrics'].items():
		for k2 in v.keys():
			if k2 != 'metric_weight':
				k2 = k2.replace('_weight', '')
				if k2 in ['velocity', 'volitility']:
					# if k == 'price':
					# 	for interval in strategy_config['price_time_interval_weights']:
					# 		metric_columns.append(k+'-'+k2+'-'+interval)
					# else:
					# 	for interval in strategy_config['fundamentals_time_interval_weights']:
					# 		metric_columns.append(k+'-'+k2+'-'+interval)						
					metric_columns.append(k+'-'+k2)
				elif k2 in ['value']:
					metric_columns.append(k+'-'+k2)
		# metric_columns.append(k+'-final_score')
	stock_df = pd.DataFrame(columns=metric_columns+['ticker'])#, 'final_score'])
	# for c in stock_df.columns: print(c)
	# # print(stock_df)
	# sys.exit()

	ciks = os.listdir(DATA_STOCKS_PATH)
	num_ciks = len(ciks)
	log.print('iterating over %d stocks (SEC CIKs):' % num_ciks,
		num_indents=0, new_line_start=True)
	for i, cik in enumerate(ciks):
		cik_path = os.path.join(DATA_STOCKS_PATH, cik)
		with open(os.path.join(cik_path, 'info.json')) as f:
			info = json.load(f)
		ticker = info['ticker']
		daily_price_history        = pd.read_csv(os.path.join(cik_path, 'daily_price_data.csv'))
		dividend_per_share_history = pd.read_csv(os.path.join(cik_path, 'dividend_per_share_history.csv'))
		fundamental_history        = pd.read_csv(os.path.join(cik_path, 'fundamentals.csv'))
		if ticker == None or \
			daily_price_history.shape[0]        in [0, 1] or \
			dividend_per_share_history.shape[0] in [0, 1] or \
			fundamental_history.shape[0]        in [0, 1]:
			continue

		log.print('cik %d of %d: %s' % (
			i, num_ciks, cik),
			num_indents=1,
			new_line_start=True)
		if verbose:
			repo_cik_path = cik_path[cik_path.index('value-investing-app'):]
			log.print(repo_cik_path, num_indents=2)
		price_data = get_velocity_and_volitility_of_price(
			daily_price_history,
			verbose=verbose,
			num_indents=3,
			new_line_start=True)
		dividends_paid_history = get_dividends_paid_history(fundamental_history)
		dividends_paid_data = get_velocity_and_volitility_of_fundamental_metric(
			'dividends_paid',
			'dividends_paid',
			dividends_paid_history,
			verbose=verbose,
			num_indents=2,
			new_line_start=True)
		book_value_history = get_book_value_history(fundamental_history)
		book_value_data = get_velocity_and_volitility_of_fundamental_metric(
			'book_value',
			'book_value',
			book_value_history,
			verbose=verbose,
			num_indents=2,
			new_line_start=True)
		net_income_history = get_net_income_history(fundamental_history)
		net_income_data = get_velocity_and_volitility_of_fundamental_metric(
			'net_income',
			'net_income',
			net_income_history,
			verbose=verbose,
			num_indents=2,
			new_line_start=True)
		dividend_yield_data = get_dividend_yield(
			i, num_ciks, info,
			verbose=verbose,
			num_indents=2,
			new_line_start=True)
		stock_df = stock_df.append(pd.DataFrame({
			'ticker'                    : ticker,
			'dividend_yield-value'      : dividend_yield_data['value'],
			'dividends_paid-velocity'   : dividends_paid_data['velocity']['weighted_average'],
			'dividends_paid-volitility' : dividends_paid_data['volitility']['weighted_average'],
			'net_income-velocity'       : net_income_data['velocity']['weighted_average'],
			'net_income-volitility'     : net_income_data['volitility']['weighted_average'],
			'price-velocity'            : price_data['velocity']['weighted_average'],
			'price-volitility'          : price_data['volitility']['weighted_average'],
			'book_value-velocity'       : book_value_data['velocity']['weighted_average'],
			'book_value-volitility'     : book_value_data['volitility']['weighted_average'],
		}, index=[cik]))
		# 	'dividends_paid_velocity-quarter'       : dividend_score_data['velocity']['quarter'],
		# 	'dividends_paid_velocity-year'          : dividend_score_data['velocity']['year'],
		# 	'dividends_paid_velocity-final_score'   : dividend_score_data['velocity']['final_score'],
		# 	'dividends_paid_volitility-quarter'     : dividend_score_data['volitility']['quarter'],
		# 	'dividends_paid_volitility-year'        : dividend_score_data['volitility']['year'],
		# 	'dividends_paid_volitility-final_score' : dividend_score_data['volitility']['final_score'],
		# 	'net_income_velocity-quarter'       : net_income_score_data['velocity']['quarter'],
		# 	'net_income_velocity-year'          : net_income_score_data['velocity']['year'],
		# 	'net_income_velocity-final_score'   : net_income_score_data['velocity']['final_score'],
		# 	'net_income_volitility-quarter'     : net_income_score_data['volitility']['quarter'],
		# 	'net_income_volitility-year'        : net_income_score_data['volitility']['year'],
		# 	'net_income_volitility-final_score' : net_income_score_data['volitility']['final_score'],
		# 	'price_velocity-day'           : price_score_data['velocity']['day'],
		# 	'price_velocity-week'          : price_score_data['velocity']['week'],
		# 	'price_velocity-month'         : price_score_data['velocity']['month'],
		# 	'price_velocity-year'          : price_score_data['velocity']['year'],
		# 	'price_velocity-final_score'   : price_score_data['velocity']['final_score'],
		# 	'price_volitility-day'         : price_score_data['volitility']['day'],
		# 	'price_volitility-week'        : price_score_data['volitility']['week'],
		# 	'price_volitility-month'       : price_score_data['volitility']['month'],
		# 	'price_volitility-year'        : price_score_data['volitility']['year'],
		# 	'price_volitility-final_score' : price_score_data['volitility']['final_score'],
		# 	'book_value_velocity-quarter'       : book_value_score_data['velocity']['quarter'],
		# 	'book_value_velocity-year'          : book_value_score_data['velocity']['year'],
		# 	'book_value_velocity-final_score'   : book_value_score_data['velocity']['final_score'],
		# 	'book_value_volitility-quarter'     : book_value_score_data['volitility']['quarter'],
		# 	'book_value_volitility-year'        : book_value_score_data['volitility']['year'],
		# 	'book_value_volitility-final_score' : book_value_score_data['volitility']['final_score'],
		# }, index=[cik]))
		if verbose:
			log.print('stock_df.loc[%s] = ' % cik, num_indents=2, new_line_start=True)
			log.print(stock_df.loc[cik].to_string(), num_indents=3)

		# input() # for testing purposes only
		if stock_df.shape[0] >= 10: break # for testing purposes only

	# # normalize data (chose the "maximum absolute scaling" method)
	# # https://www.geeksforgeeks.org/normalize-a-column-in-pandas/
	log.print('stock_df', num_indents=0, new_line_start=True)
	log.print(stock_df.to_string(), num_indents=1)
	# for k, v in strategy_config['metrics'].items():
	# 	for k2, w in v.items():
	# 		if k2 != 'metric_weight':
	# 			k2 = k2.replace('_weight', '')
	# 			if k2 in ['velocity', 'volitility']:
	# 				for interval in strategy_config['time_interval_weights']:
	# 					column = k+'_'+k2+'-'+interval
	# 					stock_df[column].normalize()
	# 					stock_df[column] = \
	# 						stock_df[column] / stock_df[column].abs().max()
	# 			else:
	# 				column = k+'_'+k2
	# 				stock_df[column] = \
	# 					stock_df[column] / stock_df[column].abs().max()
	sys.exit()

	# save to csv file
	stock_df = stock_df[[
		'ticker',
		'final_score', 
		'dividend_yield-final_score',
		'dividends_paid-final_score',
		'net_income-final_score',
		'price-final_score',
		'book_value-final_score'
	]]
	stock_df.index.name = 'cik'
	stock_df.sort_values(['final_score'], ascending=[False], inplace=True)
	save_path = os.path.join(STRATEGY_PATH, 'stock_scores.csv')
	stock_df.to_csv(save_path)
	log.print('stock scores saved to:', num_indents=0, new_line_start=True)
	log.print(save_path, num_indents=1, new_line_end=True)

