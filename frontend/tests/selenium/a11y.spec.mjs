import { Builder } from 'selenium-webdriver'
import axeBuilder from 'axe-webdriverjs'
import chrome from 'selenium-webdriver/chrome'

const TEST_BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:5173'

async function run(){
  const options = new chrome.Options()
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build()
  try{
    await driver.get(TEST_BASE_URL)
    const results = await axeBuilder(driver).withTags(['wcag2a','wcag2aa']).analyze()
    const violations = results.violations || []
    if (violations.length>0){
      console.error('A11Y violations:', violations.slice(0,5).map(v=>({id:v.id,impact:v.impact,help:v.help, nodes: v.nodes.length})))
      process.exit(2)
    }
    console.log('A11Y: OK')
    await driver.quit()
    process.exit(0)
  }catch(err){
    console.error('A11Y: ERROR', err)
    await driver.quit()
    process.exit(1)
  }
}

run()
